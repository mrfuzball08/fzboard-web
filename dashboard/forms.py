from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-input-hover',
        'placeholder': 'correo@ejemplo.com',
        'autocomplete': 'email'
    }))
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
        'class': 'form-input-hover',
        'placeholder': 'Nombre',
        'autocomplete': 'given-name'
    }))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
        'class': 'form-input-hover',
        'placeholder': 'Apellido',
        'autocomplete': 'family-name'
    }))
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-input-hover',
        'placeholder': 'Nombre de usuario',
        'autocomplete': 'username'
    }))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-input-hover',
        'placeholder': 'Contraseña',
        'autocomplete': 'new-password'
    }))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-input-hover',
        'placeholder': 'Confirmar contraseña',
        'autocomplete': 'new-password'
    }))

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={
        'class': 'form-input-hover',
        'placeholder': 'Nombre de usuario',
        'autocomplete': 'username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-input-hover',
        'placeholder': 'Contraseña',
        'autocomplete': 'current-password'
    }))


class TableTemplateForm(forms.ModelForm):
    class Meta:
        from .models import TableTemplate
        model = TableTemplate
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input-hover',
                'placeholder': 'Nombre del formato',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-input-hover',
                'placeholder': 'Descripción del formato (opcional)',
                'rows': 3,
            }),
        }
        labels = {
            'name': 'Nombre del Formato',
            'description': 'Descripción',
        }


class TemplateColumnForm(forms.ModelForm):
    class Meta:
        from .models import TemplateColumn
        model = TemplateColumn
        fields = ['name', 'data_type', 'order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input-hover',
                'placeholder': 'Nombre de columna',
            }),
            'data_type': forms.Select(attrs={
                'class': 'form-input-hover',
            }),
            'order': forms.HiddenInput(),
        }
        labels = {
            'name': 'Encabezado',
            'data_type': 'Tipo de Dato',
            'order': '',
        }


# ──────────────────────────────────────────────
#  Dataset Forms
# ──────────────────────────────────────────────

class DatasetForm(forms.ModelForm):
    """Form for creating/editing a Dataset."""
    template = forms.ModelChoiceField(
        queryset=None,  # Set dynamically in the view
        widget=forms.Select(attrs={
            'class': 'form-input-hover',
        }),
        label='Formato (Template)',
    )

    class Meta:
        from .models import Dataset
        model = Dataset
        fields = ['name', 'template']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input-hover',
                'placeholder': 'Nombre del dataset',
            }),
        }
        labels = {
            'name': 'Nombre del Dataset',
        }


class DatasetUploadForm(forms.Form):
    """Form for uploading a file to a dataset."""
    file = forms.FileField(
        label='Archivo',
        help_text='Selecciona un archivo CSV o Excel (.xlsx, .xls)',
        widget=forms.ClearableFileInput(attrs={
            'accept': '.csv,.xlsx,.xls',
            'class': 'form-input-hover',
        }),
    )
    mode = forms.ChoiceField(
        choices=[
            ('replace', 'Reemplazar — eliminar datos existentes y subir nuevos'),
            ('append', 'Agregar — mantener datos existentes y añadir nuevos'),
        ],
        initial='replace',
        widget=forms.RadioSelect(attrs={
            'class': 'form-radio',
        }),
        label='Modo de importación',
    )


# ──────────────────────────────────────────────
#  Report Forms
# ──────────────────────────────────────────────

class ReportForm(forms.ModelForm):
    """Form for creating/editing a Report."""
    dataset = forms.ModelChoiceField(
        queryset=None,  # Set dynamically in the view
        widget=forms.Select(attrs={
            'class': 'form-input-hover',
        }),
        label='Dataset',
    )

    class Meta:
        from .models import Report
        model = Report
        fields = ['name', 'description', 'dataset']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input-hover',
                'placeholder': 'Nombre del reporte',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-input-hover',
                'placeholder': 'Descripción del reporte (opcional)',
                'rows': 3,
            }),
        }
        labels = {
            'name': 'Nombre del Reporte',
            'description': 'Descripción',
        }