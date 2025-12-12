"""
QR Code Generation Module
Generate QR codes for books, user cards, and quick actions
"""
import qrcode
from io import BytesIO
from django.core.files import File
import json


class QRCodeGenerator:
    """Generate QR codes for various library entities"""
    
    @staticmethod
    def generate_book_qr(book, include_details=True):
        """Generate QR code for a book"""
        if include_details:
            data = {
                'type': 'book',
                'id': book.id,
                'title': book.title,
                'author': book.author,
                'isbn': book.isbn,
                'url': f'/books/{book.id}/'
            }
            qr_data = json.dumps(data)
        else:
            qr_data = f"BOOK:{book.id}"
        
        return QRCodeGenerator._create_qr_code(qr_data)
    
    @staticmethod
    def generate_user_card_qr(user):
        """Generate QR code for user library card"""
        data = {
            'type': 'user',
            'id': user.id,
            'username': user.username,
            'membership': user.profile.membership_type if hasattr(user, 'profile') else 'Basic',
            'url': f'/profile/'
        }
        qr_data = json.dumps(data)
        return QRCodeGenerator._create_qr_code(qr_data)
    
    @staticmethod
    def generate_borrow_qr(borrow_record):
        """Generate QR code for borrow transaction"""
        data = {
            'type': 'borrow',
            'id': borrow_record.id,
            'book': borrow_record.book.title,
            'user': borrow_record.user.username,
            'due_date': str(borrow_record.due_date),
            'url': f'/borrow-history/'
        }
        qr_data = json.dumps(data)
        return QRCodeGenerator._create_qr_code(qr_data)
    
    @staticmethod
    def generate_quick_action_qr(action, book_id=None):
        """Generate QR code for quick actions (borrow, return, reserve)"""
        data = {
            'type': 'action',
            'action': action,
            'book_id': book_id,
            'url': f'/{action}/{book_id}/' if book_id else f'/{action}/'
        }
        qr_data = json.dumps(data)
        return QRCodeGenerator._create_qr_code(qr_data)
    
    @staticmethod
    def _create_qr_code(data, size=10, border=2):
        """Internal method to create QR code image"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=size,
            border=border,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to BytesIO
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return buffer
    
    @staticmethod
    def save_qr_to_file(qr_buffer, filename):
        """Save QR code buffer to file"""
        return File(qr_buffer, name=filename)
