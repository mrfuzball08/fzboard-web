import csv
from django.db import IntegrityError, transaction

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.forms import modelformset_factory
from django.http import HttpResponse

from .forms import CustomUserCreationForm, LoginForm, TableTemplateForm, TemplateColumnForm
from .models import TableTemplate, TemplateColumn


@login_required
def dashboard(request):
    return render(request, 'dashboard/dashboard.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '¡Cuenta creada exitosamente!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'dashboard/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, '¡Bienvenido de vuelta!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Nombre de usuario o contraseña incorrectos.')
        else:
            messages.error(request, 'Por favor completa todos los campos.')
    else:
        form = LoginForm()
    
    return render(request, 'dashboard/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'Has cerrado sesión exitosamente.')
    return redirect('login')


# ──────────────────────────────────────────────
#  Template Management Views
# ──────────────────────────────────────────────

@login_required
def template_list(request):
    """List all templates owned by the current user, with optional search."""
    templates = TableTemplate.objects.filter(owner=request.user)

    query = request.GET.get('q', '').strip()
    if query:
        templates = templates.filter(name__icontains=query)

    return render(request, 'dashboard/templates_list.html', {
        'templates': templates,
        'query': query,
    })


@login_required
def template_create(request):
    """Create a new template with its columns."""
    ColumnFormSet = modelformset_factory(
        TemplateColumn,
        form=TemplateColumnForm,
        extra=0,
        can_delete=True,
    )

    if request.method == 'POST':
        form = TableTemplateForm(request.POST)
        formset = ColumnFormSet(request.POST, queryset=TemplateColumn.objects.none())

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    template = form.save(commit=False)
                    template.owner = request.user
                    template.save()

                    for i, col_form in enumerate(formset):
                        if col_form.cleaned_data and not col_form.cleaned_data.get('DELETE', False):
                            column = col_form.save(commit=False)
                            column.template = template
                            column.order = i
                            column.save()

                messages.success(request, f'¡Formato "{template.name}" creado exitosamente!')
                return redirect('template_detail', pk=template.pk)
            except IntegrityError:
                form.add_error('name', 'Ya tienes un formato con este nombre. Elige un nombre diferente.')
                messages.error(request, 'Ya existe un formato con ese nombre.')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = TableTemplateForm()
        formset = ColumnFormSet(queryset=TemplateColumn.objects.none())

    return render(request, 'dashboard/template_create.html', {
        'form': form,
        'formset': formset,
    })


@login_required
def template_detail(request, pk):
    """View details and edit a specific template."""
    from django.forms import inlineformset_factory
    template = get_object_or_404(TableTemplate, pk=pk, owner=request.user)
    
    ColumnFormSet = inlineformset_factory(
        TableTemplate,
        TemplateColumn,
        form=TemplateColumnForm,
        extra=0,
        can_delete=True,
    )

    if request.method == 'POST':
        form = TableTemplateForm(request.POST, instance=template)
        formset = ColumnFormSet(request.POST, instance=template, prefix='form')
        
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, f'¡Formato "{template.name}" actualizado exitosamente!')
            return redirect('template_detail', pk=template.pk)
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = TableTemplateForm(instance=template)
        formset = ColumnFormSet(instance=template, prefix='form')

    columns = template.columns.all()
    owner = template.owner
    owner_name = owner.get_full_name() or owner.username
    
    return render(request, 'dashboard/template_detail.html', {
        'template': template,
        'columns': columns,
        'column_count': columns.count(),
        'owner_name': owner_name,
        'form': form,
        'formset': formset,
    })


@login_required
def template_delete(request, pk):
    """Delete a template."""
    template = get_object_or_404(TableTemplate, pk=pk, owner=request.user)

    if request.method == 'POST':
        name = template.name
        template.delete()
        messages.success(request, f'Formato "{name}" eliminado exitosamente.')
        return redirect('template_list')

    return render(request, 'dashboard/template_delete.html', {'template': template})


@login_required
def template_download_csv(request, pk):
    """Generate and download a CSV file from a template definition."""
    template = get_object_or_404(TableTemplate, pk=pk, owner=request.user)
    columns = template.columns.all()

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{template.name}.csv"'
    response.write('\ufeff')  # UTF-8 BOM for Excel compatibility

    writer = csv.writer(response)

    # Write header row with column names
    headers = [col.name for col in columns]
    writer.writerow(headers)

    # Write data type hint row (helpful for users filling the template)
    type_hints = [col.get_data_type_display() for col in columns]
    writer.writerow(type_hints)

    return response
