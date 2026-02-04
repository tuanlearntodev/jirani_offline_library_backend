from importlib.metadata import metadata
from fastapi import UploadFile, HTTPException
from pathlib import Path
import uuid
from typing import Optional
from app.repositories import BookRepo
from app import settings
from app.schemas import BookDetail, BookRead, BookCreate, BookUpload, BookBase, TagCreate
import re
import fitz  # PyMuPDF


class BookService:
    def __init__(self, book_repo: BookRepo):
        self.book_repo = book_repo
        self.cover_path = settings.COVER_DIR
        self.upload_path = settings.UPLOAD_DIR
        self.max_upload_size = settings.MAX_UPLOAD_SIZE
        self.max_cover_size = settings.MAX_COVER_SIZE
        
        # Create upload directories if they don't exist
        self.upload_path.mkdir(parents=True, exist_ok=True)
        self.cover_path.mkdir(parents=True, exist_ok=True)
    
    def get_book_by_uid(self, book_uid: str) -> Optional[BookDetail]:
        book = self.book_repo.get_book_by_uid(book_uid)
        if not book:
            return None
        return BookDetail.model_validate(book)
    
    def get_all_books(self) -> list[BookRead]:
        books = self.book_repo.get_all_books()
        return [BookRead.model_validate(book) for book in books]
    
    @staticmethod
    def _file_name_generator(title: str, uid: str, extension: str) -> str:
        """Generate a safe filename from title, UID and extension"""
        clean_title = re.sub(r'[^\w\s-]', '', title).strip().lower()
        clean_title = re.sub(r'[-\s]+', '_', clean_title)
        
        return f"{clean_title}_{uid}.{extension}"
    
    async def upload_book(self, metadata: BookUpload, file: UploadFile, cover: Optional[UploadFile] = None) -> BookBase:
        """Upload book and cover with validation and error handling"""
        if not metadata.title or not metadata.title.strip():
            # Get filename without extension: "lesson_1.pdf" -> "lesson_1"
            raw_name = Path(file.filename).stem 
            # Replace underscores/dashes with spaces and capitalize for a "clean" look
            metadata.title = raw_name.replace('_', ' ').replace('-', ' ').title().strip()
        # Validate file parameter
        if not file:
            raise HTTPException(status_code=400, detail="Book file is required")
        if not file.filename:
            raise HTTPException(status_code=400, detail="Book filename is required")
        
        # Validate file extension
        if '.' not in file.filename:
            raise HTTPException(status_code=400, detail="Book file must have an extension")
        
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type '.{file_extension}'. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
        
        # Read and validate book file header
        file_header = await file.read(8192)  # Read first 8KB for validation
        if len(file_header) == 0:
            raise HTTPException(status_code=400, detail="Book file is empty")
        
        # Validate book file content type from header
        self._validate_book_content(file_header, file_extension)
        
        # Generate unique ID and filename
        book_uid = str(uuid.uuid4())[:8]
        file_name = self._file_name_generator(metadata.title, book_uid, file_extension)
        file_path = self.upload_path / file_name
        
        # Variables for cleanup
        saved_file_path = None
        saved_cover_path = None
        
        try:
            # Save book file while checking size
            total_size = len(file_header)
            with file_path.open("wb") as buffer:
                # Write the header we already read
                buffer.write(file_header)
                
                # Stream the rest of the file in chunks
                while True:
                    chunk = await file.read(8192)  # 8KB chunks
                    if not chunk:
                        break
                    total_size += len(chunk)
                    if total_size > self.max_upload_size:
                        raise HTTPException(
                            status_code=400,
                            detail=f"File too large ({total_size / (1024*1024):.2f}MB). Max: {self.max_upload_size / (1024*1024):.0f}MB"
                        )
                    buffer.write(chunk)
            
            saved_file_path = file_path
            
            # Handle cover upload if provided
            if cover and cover.filename:
                # Validate cover extension
                if '.' not in cover.filename:
                    raise HTTPException(status_code=400, detail="Cover file must have an extension")
                
                cover_extension = cover.filename.split('.')[-1].lower()
                if cover_extension not in settings.ALLOWED_IMAGE_EXTENSIONS:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid cover type '.{cover_extension}'. Allowed: {', '.join(settings.ALLOWED_IMAGE_EXTENSIONS)}"
                    )
                
                # Read and validate cover header
                cover_header = await cover.read(8192)  # Read first 8KB
                if len(cover_header) == 0:
                    raise HTTPException(status_code=400, detail="Cover file is empty")
                
                # Validate cover content type
                self._validate_image_content(cover_header, cover_extension)
                
                # Save cover file while checking size
                cover_name = f"{book_uid}.{cover_extension}"
                cover_path = self.cover_path / cover_name
                total_cover_size = len(cover_header)
                
                with cover_path.open("wb") as buffer:
                    # Write the header we already read
                    buffer.write(cover_header)
                    
                    # Stream the rest of the file
                    while True:
                        chunk = await cover.read(8192)
                        if not chunk:
                            break
                        total_cover_size += len(chunk)
                        if total_cover_size > self.max_cover_size:
                            raise HTTPException(
                                status_code=400,
                                detail=f"Cover too large ({total_cover_size / (1024*1024):.2f}MB). Max: {self.max_cover_size / (1024*1024):.0f}MB"
                            )
                        buffer.write(chunk)
                
                saved_cover_path = cover_path
            else: 
                cover_name = f"{book_uid}.jpg"
                gen_cover_path = self.cover_path / cover_name
                
                # Use our helper to extract from the file we just saved to disk
                self._generate_thumbnail(file_path, gen_cover_path, file_extension)
                saved_cover_path = gen_cover_path
            
            extracted_tags = []
            if file_extension == "epub":
                extracted_tags = self._extract_epub_tags(file_path)
            all_tag_names = {t.name.lower(): t for t in metadata.tags}
            for t_name in extracted_tags:
                if t_name.lower() not in all_tag_names:
                    all_tag_names[t_name.lower()] = TagCreate(name=t_name)
            
            final_tags = list(all_tag_names.values())
            # Create book data for database
            book_data = BookCreate(
                title=metadata.title,
                uid=book_uid,
                file_type=file.content_type or f"application/{file_extension}",
                extension=file_extension,
                file_path=file_name,  # Store relative path, not absolute
                cover_path=cover_name,  # Store relative path, not absolute
                tags=final_tags
            )
            
            # Save to database
            created_book = self.book_repo.create_book(book_data)
            return BookBase.model_validate(created_book)
            
        except HTTPException:
            # Clean up uploaded files on validation error
            if saved_file_path and saved_file_path.exists():
                saved_file_path.unlink()
            if saved_cover_path and saved_cover_path.exists():
                saved_cover_path.unlink()
            raise
        except Exception as e:
            # Clean up uploaded files on any error
            if saved_file_path and saved_file_path.exists():
                saved_file_path.unlink()
            if saved_cover_path and saved_cover_path.exists():
                saved_cover_path.unlink()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload book: {str(e)}"
            )
    
    async def update_book(self, book_uid: str, metadata: BookUpload, cover: Optional[UploadFile] = None) -> BookBase:
        existing_book = self.book_repo.get_book_by_uid(book_uid)
        if not existing_book:
            raise HTTPException(status_code=404, detail="Book not found")
        
        # Update title if provided
        if metadata.title and metadata.title.strip():
            existing_book.title = metadata.title.strip()        
        
        # Handle cover update if provided
        if cover and cover.filename:
            # Delete old cover image if it exists
            if existing_book.cover_path:
                old_cover_path = self.cover_path / existing_book.cover_path
                if old_cover_path.exists():
                    try:
                        old_cover_path.unlink()
                    except Exception as e:
                        print(f"Warning: Failed to delete old cover: {e}")
            
            # Validate cover extension
            if '.' not in cover.filename:
                raise HTTPException(status_code=400, detail="Cover file must have an extension")
            
            cover_extension = cover.filename.split('.')[-1].lower()
            if cover_extension not in settings.ALLOWED_IMAGE_EXTENSIONS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid cover type '.{cover_extension}'. Allowed: {', '.join(settings.ALLOWED_IMAGE_EXTENSIONS)}"
                )
            
            # Read and validate cover header
            cover_header = await cover.read(8192)  # Read first 8KB
            if len(cover_header) == 0:
                raise HTTPException(status_code=400, detail="Cover file is empty")
            
            # Validate cover content type
            self._validate_image_content(cover_header, cover_extension)
            
            # Save new cover file while checking size
            cover_name = f"{book_uid}.{cover_extension}"
            cover_path = self.cover_path / cover_name
            total_cover_size = len(cover_header)
            
            with cover_path.open("wb") as buffer:
                # Write the header we already read
                buffer.write(cover_header)
                
                # Stream the rest of the file
                while True:
                    chunk = await cover.read(8192)
                    if not chunk:
                        break
                    total_cover_size += len(chunk)
                    if total_cover_size > self.max_cover_size:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Cover too large ({total_cover_size / (1024*1024):.2f}MB). Max: {self.max_cover_size / (1024*1024):.0f}MB"
                        )
                    buffer.write(chunk)
            
            existing_book.cover_path = cover_name
        if metadata.tags is not None:
            all_tag_names = {t.name.lower(): t for t in metadata.tags}
            final_tags = list(all_tag_names.values())
        else:
            final_tags = [TagCreate(name=t.name) for t in existing_book.tags]
        book_updated = BookCreate(
            title=existing_book.title,  
            uid=existing_book.uid,
            file_type=existing_book.file_type,
            extension=existing_book.extension,
            file_path=existing_book.file_path,
            cover_path=existing_book.cover_path,
            tags=final_tags
        )
        # Save updates to database
        try:    
            updated_book = self.book_repo.update_book(book_uid, book_updated)
            return BookBase.model_validate(updated_book)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update book: {str(e)}"
            )
            
            
    def delete_book(self, book_uid: str) -> None:
        existing_book = self.book_repo.get_book_by_uid(book_uid)
        if not existing_book:
            raise HTTPException(status_code=404, detail="Book not found")
        
        # Delete book file
        book_path = self.upload_path / existing_book.file_path
        if book_path.exists():
            try:
                book_path.unlink()
            except Exception as e:
                print(f"Warning: Failed to delete book file: {e}")
        
        # Delete cover file
        if existing_book.cover_path:
            cover_path = self.cover_path / existing_book.cover_path
            if cover_path.exists():
                try:
                    cover_path.unlink()
                except Exception as e:
                    print(f"Warning: Failed to delete cover file: {e}")
        
        # Delete from database
        try:
            self.book_repo.delete_book(book_uid)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete book: {str(e)}"
            )
    
    def _validate_book_content(self, content: bytes, extension: str):
        """Validate book file content matches its extension"""
        # Check PDF signature
        if extension == "pdf":
            if not content.startswith(b"%PDF-"):
                raise HTTPException(
                    status_code=400,
                    detail="File does not appear to be a valid PDF"
                )
        # Check EPUB signature (it's a ZIP file)
        elif extension == "epub":
            if not content.startswith(b"PK\x03\x04"):
                raise HTTPException(
                    status_code=400,
                    detail="File does not appear to be a valid EPUB"
                )
    
    def _validate_image_content(self, content: bytes, extension: str):
        image_signatures = {
            "jpg": b"\xff\xd8\xff",
            "jpeg": b"\xff\xd8\xff",
            "png": b"\x89PNG\r\n\x1a\n",
            "webp": b"RIFF" # WEBP starts with RIFF then WEBP at offset 8
        }
        
        sig = image_signatures.get(extension)
        if sig and not content.startswith(sig):
            raise HTTPException(
                status_code=400,
                detail=f"File does not appear to be a valid {extension.upper()} image"
            )
            
    def _generate_thumbnail(self, book_path: Path, output_path: Path, extension: str) -> bool:
        """Extracts cover: PDF uses first page, EPUB uses embedded metadata image."""
        try:
            doc = fitz.open(str(book_path))
            
            if extension == "pdf":
                # PDFs don't have 'metadata images', so we render the first page
                page = doc.load_page(0)
                print("Generating thumbnail for PDF")
                pix = page.get_pixmap(matrix=fitz.Matrix(0.5, 0.5))
                pix.save(str(output_path))
                doc.close()
                return True
                
            elif extension == "epub":
                # Get the embedded cover image from EPUB metadata
                image_tuple = doc.get_cover_image()
                
                if image_tuple:
                    img_bytes, _ = image_tuple # Unpack the bytes
                    with open(output_path, "wb") as f:
                        f.write(img_bytes)
                    doc.close()
                    return True
                
                # Fallback: if no metadata cover exists, render the first page
                page = doc.load_page(0)
                pix = page.get_pixmap(matrix=fitz.Matrix(0.5, 0.5))
                pix.save(str(output_path))
                doc.close()
                return True
                
            return False
        except Exception as e:
            print(f"Thumbnail extraction failed: {e}")
            return False
        
        
    def _extract_epub_tags(self, book_path: Path) -> list[str]:
        """Extracts subjects/tags from EPUB metadata."""
        try:
            doc = fitz.open(str(book_path))
            # Get 'subject' string: "History, Africa, Economy"
            subjects = doc.metadata.get("subject", "")
            doc.close()
            
            if subjects:
                # Split by comma or semicolon and clean up whitespace
                return [t.strip() for t in re.split(r'[,;]+', subjects) if t.strip()]
            return []
        except Exception as e:
            print(f"Tag extraction failed: {e}")
            return []
        