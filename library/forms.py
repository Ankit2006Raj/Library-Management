from django import forms
from .models import Book

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = [
            'title', 'author', 'published_year', 'category', 'isbn', 
            'publisher', 'language', 'pages', 'edition', 'description',
            'status', 'copies_available', 'total_copies', 'shelf_location', 'rating'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter book title',
                'required': True
            }),
            'author': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter author name',
                'required': True
            }),
            'published_year': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter publication year',
                'required': True
            }),
            'category': forms.Select(attrs={
                'class': 'form-input'
            }),
            'isbn': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter ISBN (optional)'
            }),
            'publisher': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter publisher name (optional)'
            }),
            'language': forms.Select(attrs={
                'class': 'form-input'
            }),
            'pages': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Number of pages (optional)'
            }),
            'edition': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Edition (e.g., 1st, 2nd) (optional)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Enter book description (optional)',
                'rows': 4
            }),
            'status': forms.Select(attrs={
                'class': 'form-input'
            }),
            'copies_available': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 0
            }),
            'total_copies': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 1
            }),
            'shelf_location': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., A-12, B-05 (optional)'
            }),
            'rating': forms.NumberInput(attrs={
                'class': 'form-input',
                'step': '0.01',
                'min': '0',
                'max': '5',
                'placeholder': '0.00 - 5.00'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        copies_available = cleaned_data.get('copies_available')
        total_copies = cleaned_data.get('total_copies')
        
        if copies_available and total_copies:
            if copies_available > total_copies:
                raise forms.ValidationError(
                    "Available copies cannot exceed total copies."
                )
        
        return cleaned_data



from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, Review, BorrowRecord


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-input',
        'placeholder': 'Enter your email'
    }))
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'form-input',
        'placeholder': 'Enter your first name'
    }))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'form-input',
        'placeholder': 'Enter your last name'
    }))
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Choose a username'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-input'})
        self.fields['password2'].widget.attrs.update({'class': 'form-input'})


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone', 'address', 'date_of_birth', 'profile_picture']
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter phone number'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Enter your address',
                'rows': 3
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-input'
            }),
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'title', 'comment']
        widgets = {
            'rating': forms.Select(
                choices=[(i, f'{i} Star{"s" if i > 1 else ""}') for i in range(1, 6)],
                attrs={'class': 'form-input'}
            ),
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Review title'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Write your review...',
                'rows': 5
            }),
        }


class BorrowBookForm(forms.Form):
    borrow_days = forms.IntegerField(
        min_value=1,
        max_value=30,
        initial=14,
        label='Borrow Duration (days)',
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': 'Number of days (1-30)'
        })
    )
