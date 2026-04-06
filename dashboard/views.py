import csv
import json

from django.db import IntegrityError, transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.forms import modelformset_factory
from django.http import HttpResponse, JsonResponse

from .forms import (
    CustomUserCreationForm, LoginForm, TableTemplateForm, TemplateColumnForm,
    DatasetForm, DatasetUploadForm, ReportForm,
)
from .models import (
    TableTemplate, TemplateColumn, Dataset, DatasetImport, DatasetRow,
    Report, ReportWidget, ReportFilter,
)


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


# ──────────────────────────────────────────────
#  Dataset Management Views
# ──────────────────────────────────────────────

@login_required
def dataset_list(request):
    """List all datasets owned by the current user, with optional search."""
    datasets = Dataset.objects.filter(owner=request.user, is_archived=False)

    query = request.GET.get('q', '').strip()
    if query:
        datasets = datasets.filter(name__icontains=query)

    return render(request, 'dashboard/datasets_list.html', {
        'datasets': datasets,
        'query': query,
    })


@login_required
def dataset_create(request):
    """Create a new dataset linked to one of the user's templates."""
    if request.method == 'POST':
        form = DatasetForm(request.POST)
        form.fields['template'].queryset = TableTemplate.objects.filter(owner=request.user)

        if form.is_valid():
            try:
                with transaction.atomic():
                    dataset = form.save(commit=False)
                    dataset.owner = request.user
                    dataset.save()
                messages.success(request, f'¡Dataset "{dataset.name}" creado exitosamente!')
                return redirect('dataset_detail', pk=dataset.pk)
            except IntegrityError:
                form.add_error('name', 'Ya tienes un dataset con este nombre para este formato.')
                messages.error(request, 'Ya existe un dataset con ese nombre para este formato.')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = DatasetForm()
        form.fields['template'].queryset = TableTemplate.objects.filter(owner=request.user)

    return render(request, 'dashboard/dataset_create.html', {
        'form': form,
    })


@login_required
def dataset_detail(request, pk):
    """View details of a specific dataset with import history and data preview."""
    dataset = get_object_or_404(Dataset, pk=pk, owner=request.user)
    imports = dataset.imports.all()[:10]
    columns = dataset.template.columns.all()

    # Data preview: first 25 rows
    preview_rows = dataset.rows.all()[:25]

    # Build preview data with column names
    preview_data = []
    for row in preview_rows:
        row_cells = []
        for col in columns:
            cell_value = row.data_json.get(str(col.id))
            has_issue = row.issues.filter(template_column=col).exists() if not row.is_valid else False
            row_cells.append({
                'value': cell_value,
                'has_issue': has_issue,
            })
        preview_data.append({
            'index': row.row_index,
            'cells': row_cells,
            'is_valid': row.is_valid,
            'issue_count': row.issue_count,
        })

    return render(request, 'dashboard/dataset_detail.html', {
        'dataset': dataset,
        'imports': imports,
        'columns': columns,
        'preview_data': preview_data,
        'total_rows': dataset.row_count,
    })


@login_required
def dataset_upload(request, pk):
    """
    Upload a file to a dataset.
    GET: Show upload wizard page.
    POST: Receive file + mapping + mode, execute import.
    """
    dataset = get_object_or_404(Dataset, pk=pk, owner=request.user)
    template_columns = dataset.template.columns.all()

    if request.method == 'POST':
        # Handle the upload + import execution
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            messages.error(request, 'No se seleccionó ningún archivo.')
            return redirect('dataset_upload', pk=dataset.pk)

        mode = request.POST.get('mode', 'replace')
        mapping_json = request.POST.get('header_mapping', '{}')

        try:
            header_mapping = json.loads(mapping_json)
            # Convert string values to int where applicable
            clean_mapping = {}
            for k, v in header_mapping.items():
                if v is not None and v != '' and v != 'null':
                    clean_mapping[k] = int(v)
                else:
                    clean_mapping[k] = None
        except (json.JSONDecodeError, ValueError):
            messages.error(request, 'Error en el mapeo de columnas.')
            return redirect('dataset_upload', pk=dataset.pk)

        # Read the file
        from dashboard.services.import_readers import read_upload_to_dataframe
        from dashboard.services.import_executor import execute_import

        try:
            df = read_upload_to_dataframe(uploaded_file)
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('dataset_upload', pk=dataset.pk)
        except Exception as e:
            messages.error(request, f'Error al leer el archivo: {str(e)}')
            return redirect('dataset_upload', pk=dataset.pk)

        # Create import record
        dataset_import = DatasetImport.objects.create(
            dataset=dataset,
            source_filename=uploaded_file.name,
            source_file=uploaded_file,
            mode=mode,
            status='pending',
            header_mapping_json=clean_mapping,
        )

        try:
            execute_import(dataset, df, clean_mapping, mode, dataset_import)
            messages.success(
                request,
                f'¡Importación completada! {dataset_import.inserted_rows} filas importadas'
                f'{f", {dataset_import.invalid_rows} con problemas" if dataset_import.invalid_rows else ""}.'
            )
        except Exception as e:
            messages.error(request, f'Error durante la importación: {str(e)}')

        return redirect('dataset_detail', pk=dataset.pk)

    # GET: Render the upload wizard page
    columns_data = [
        {'id': col.id, 'name': col.name, 'data_type': col.data_type,
         'data_type_display': col.get_data_type_display()}
        for col in template_columns
    ]

    return render(request, 'dashboard/dataset_upload.html', {
        'dataset': dataset,
        'columns_json': json.dumps(columns_data),
    })


@login_required
def dataset_upload_mapping(request, pk):
    """
    API endpoint: receives file headers, returns suggested mapping.
    POST with JSON body: { "headers": ["col1", "col2", ...] }
    Returns JSON: { "mapping": {...}, "extra_columns": [...], "missing_columns": [...] }
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Solo POST permitido'}, status=405)

    dataset = get_object_or_404(Dataset, pk=pk, owner=request.user)
    template_columns = dataset.template.columns.all()

    try:
        body = json.loads(request.body)
        file_headers = body.get('headers', [])
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    from dashboard.services.import_mapping import suggest_mapping
    result = suggest_mapping(file_headers, template_columns)

    return JsonResponse(result)


@login_required
def dataset_import_detail(request, pk, import_pk):
    """View details of a specific import event."""
    dataset = get_object_or_404(Dataset, pk=pk, owner=request.user)
    dataset_import = get_object_or_404(DatasetImport, pk=import_pk, dataset=dataset)

    # Get template columns for header display
    template_columns = dataset.template.columns.all()
    columns_by_id = {tc.id: tc for tc in template_columns}

    # Build mapping display
    mapping_display = []
    for file_header, col_id in dataset_import.header_mapping_json.items():
        tc = columns_by_id.get(col_id) if col_id else None
        mapping_display.append({
            'file_header': file_header,
            'template_column': tc.name if tc else '— Sin mapear —',
            'data_type': tc.get_data_type_display() if tc else '',
            'is_mapped': col_id is not None,
        })

    # Issue summary
    from django.db.models import Count
    issue_summary = DatasetRow.objects.filter(
        dataset_import=dataset_import, is_valid=False
    ).aggregate(total_invalid=Count('id'))

    return render(request, 'dashboard/dataset_import_detail.html', {
        'dataset': dataset,
        'import_obj': dataset_import,
        'mapping_display': mapping_display,
        'issue_summary': issue_summary,
    })


@login_required
def dataset_delete(request, pk):
    """Delete a dataset."""
    dataset = get_object_or_404(Dataset, pk=pk, owner=request.user)

    if request.method == 'POST':
        name = dataset.name
        dataset.delete()
        messages.success(request, f'Dataset "{name}" eliminado exitosamente.')
        return redirect('dataset_list')

    return render(request, 'dashboard/dataset_delete.html', {'dataset': dataset})


# ──────────────────────────────────────────────
#  Report Management Views
# ──────────────────────────────────────────────

@login_required
def report_list(request):
    """List all reports owned by the current user, with optional search."""
    reports = Report.objects.filter(owner=request.user, is_archived=False).select_related('dataset', 'dataset__template')

    query = request.GET.get('q', '').strip()
    if query:
        reports = reports.filter(name__icontains=query)

    return render(request, 'dashboard/reports_list.html', {
        'reports': reports,
        'query': query,
    })


@login_required
def report_create(request):
    """Create a new report linked to one of the user's datasets."""
    if request.method == 'POST':
        form = ReportForm(request.POST)
        form.fields['dataset'].queryset = Dataset.objects.filter(owner=request.user, status='ready')

        if form.is_valid():
            try:
                with transaction.atomic():
                    report = form.save(commit=False)
                    report.owner = request.user
                    report.save()
                messages.success(request, f'¡Reporte "{report.name}" creado exitosamente!')
                return redirect('report_builder', pk=report.pk)
            except IntegrityError:
                form.add_error('name', 'Ya tienes un reporte con este nombre para este dataset.')
                messages.error(request, 'Ya existe un reporte con ese nombre para este dataset.')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = ReportForm()
        form.fields['dataset'].queryset = Dataset.objects.filter(owner=request.user, status='ready')

    return render(request, 'dashboard/report_create.html', {
        'form': form,
    })


@login_required
def report_detail(request, pk):
    """
    Report viewer: renders all widgets with live data.
    Executes the query engine for each widget and passes results to the template.
    """
    report = get_object_or_404(Report, pk=pk, owner=request.user)
    widgets = report.widgets.all()

    from dashboard.services.report_query import execute_widget
    from dataclasses import asdict

    widget_results = []
    for widget in widgets:
        result = execute_widget(widget, report)
        widget_results.append({
            'widget': widget,
            'result': asdict(result),
        })

    return render(request, 'dashboard/report_detail.html', {
        'report': report,
        'widget_results': widget_results,
        'widget_results_json': json.dumps([wr['result'] for wr in widget_results]),
        'widgets_meta_json': json.dumps([{
            'id': wr['widget'].id,
            'title': wr['widget'].title,
            'widget_type': wr['widget'].widget_type,
        } for wr in widget_results]),
    })


@login_required
def report_builder(request, pk):
    """
    Report builder page: mounts the Svelte ReportBuilder island.
    Passes report data, dataset columns, existing widgets, and filters.
    """
    report = get_object_or_404(Report, pk=pk, owner=request.user)

    from dashboard.services.report_fields import get_all_field_info

    fields = get_all_field_info(report.dataset)
    widgets = list(report.widgets.values(
        'id', 'title', 'widget_type', 'config_json', 'sort_order',
    ))
    filters = list(report.filters.values(
        'id', 'field_kind', 'field_ref', 'operator', 'value_json', 'sort_order',
    ))

    return render(request, 'dashboard/report_builder.html', {
        'report': report,
        'builder_data_json': json.dumps({
            'reportPk': report.pk,
            'reportName': report.name,
            'datasetName': report.dataset.name,
            'templateName': report.dataset.template.name,
            'fields': fields,
            'widgets': widgets,
            'filters': filters,
            'csrf': str(request.META.get('CSRF_COOKIE', '')),
        }),
    })


@login_required
def report_delete(request, pk):
    """Delete a report."""
    report = get_object_or_404(Report, pk=pk, owner=request.user)

    if request.method == 'POST':
        name = report.name
        report.delete()
        messages.success(request, f'Reporte "{name}" eliminado exitosamente.')
        return redirect('report_list')

    return render(request, 'dashboard/report_delete.html', {'report': report})


@login_required
def report_widget_api(request, pk, widget_pk=None):
    """
    JSON API for CRUD operations on report widgets.
    POST: create new widget
    PUT: update existing widget
    DELETE: delete widget
    """
    report = get_object_or_404(Report, pk=pk, owner=request.user)

    if request.method == 'POST':
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)

        widget = ReportWidget.objects.create(
            report=report,
            title=body.get('title', 'Nuevo Widget'),
            widget_type=body.get('widget_type', 'table'),
            config_json=body.get('config_json', {}),
            sort_order=body.get('sort_order', report.widgets.count()),
        )
        return JsonResponse({
            'id': widget.id,
            'title': widget.title,
            'widget_type': widget.widget_type,
            'config_json': widget.config_json,
            'sort_order': widget.sort_order,
        }, status=201)

    elif request.method == 'PUT':
        if not widget_pk:
            return JsonResponse({'error': 'widget_pk requerido'}, status=400)
        widget = get_object_or_404(ReportWidget, pk=widget_pk, report=report)
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)

        if 'title' in body:
            widget.title = body['title']
        if 'widget_type' in body:
            widget.widget_type = body['widget_type']
        if 'config_json' in body:
            widget.config_json = body['config_json']
        if 'sort_order' in body:
            widget.sort_order = body['sort_order']
        widget.save()

        return JsonResponse({
            'id': widget.id,
            'title': widget.title,
            'widget_type': widget.widget_type,
            'config_json': widget.config_json,
            'sort_order': widget.sort_order,
        })

    elif request.method == 'DELETE':
        if not widget_pk:
            return JsonResponse({'error': 'widget_pk requerido'}, status=400)
        widget = get_object_or_404(ReportWidget, pk=widget_pk, report=report)
        widget.delete()
        return JsonResponse({'ok': True})

    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required
def report_filter_api(request, pk, filter_pk=None):
    """
    JSON API for CRUD operations on report-level filters.
    POST: create new filter
    PUT: update existing filter
    DELETE: delete filter
    """
    report = get_object_or_404(Report, pk=pk, owner=request.user)

    if request.method == 'POST':
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)

        rf = ReportFilter.objects.create(
            report=report,
            field_kind=body.get('field_kind', 'template_column'),
            field_ref=body.get('field_ref', 0),
            operator=body.get('operator', 'equals'),
            value_json=body.get('value_json', {}),
            sort_order=body.get('sort_order', report.filters.count()),
        )
        return JsonResponse({
            'id': rf.id,
            'field_kind': rf.field_kind,
            'field_ref': rf.field_ref,
            'operator': rf.operator,
            'value_json': rf.value_json,
            'sort_order': rf.sort_order,
        }, status=201)

    elif request.method == 'PUT':
        if not filter_pk:
            return JsonResponse({'error': 'filter_pk requerido'}, status=400)
        rf = get_object_or_404(ReportFilter, pk=filter_pk, report=report)
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)

        if 'field_kind' in body:
            rf.field_kind = body['field_kind']
        if 'field_ref' in body:
            rf.field_ref = body['field_ref']
        if 'operator' in body:
            rf.operator = body['operator']
        if 'value_json' in body:
            rf.value_json = body['value_json']
        if 'sort_order' in body:
            rf.sort_order = body['sort_order']
        rf.save()

        return JsonResponse({
            'id': rf.id,
            'field_kind': rf.field_kind,
            'field_ref': rf.field_ref,
            'operator': rf.operator,
            'value_json': rf.value_json,
            'sort_order': rf.sort_order,
        })

    elif request.method == 'DELETE':
        if not filter_pk:
            return JsonResponse({'error': 'filter_pk requerido'}, status=400)
        rf = get_object_or_404(ReportFilter, pk=filter_pk, report=report)
        rf.delete()
        return JsonResponse({'ok': True})

    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required
def report_widget_preview(request, pk):
    """
    JSON API: Execute the query engine for a widget config and return results.
    POST with JSON body: { "widget_type": "bar", "config_json": {...} }
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Solo POST permitido'}, status=405)

    report = get_object_or_404(Report, pk=pk, owner=request.user)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    # Validate first
    widget_type = body.get('widget_type', 'table')
    config_json = body.get('config_json', {})

    from dashboard.services.report_validation import validate_widget_config
    is_valid, errors = validate_widget_config(widget_type, config_json, report.dataset)

    if not is_valid:
        return JsonResponse({'errors': errors}, status=400)

    # Execute query
    from dashboard.services.report_query import execute_widget
    from dataclasses import asdict

    widget_dict = {
        'widget_type': widget_type,
        'config_json': config_json,
    }
    result = execute_widget(widget_dict, report)

    return JsonResponse(asdict(result))

