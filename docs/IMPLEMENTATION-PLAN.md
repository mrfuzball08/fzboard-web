# Report System Implementation Plan

## Objective

Build a reporting pipeline on top of the existing `TableTemplate` model so users can:

1. Define a schema with `TableTemplate` and `TemplateColumn`
2. Upload CSV or Excel files against that schema
3. Store imported rows even when some cells are invalid
4. Build reports using filters, groupings, aggregations, and calculated fields
5. Render report widgets in a structured builder first
6. Export report results to CSV, Excel, and PDF

This plan follows these product decisions:

- One dataset belongs to one template
- Extra file columns are flagged and ignored by default
- Missing template columns are stored as `null` and marked as issues
- Upload flow allows manual header mapping
- Reports surface invalid data warnings in the builder and results
- Formula references use stable IDs internally and labels in the UI
- No deduplication in v1

## Current Baseline

The project already has:

- `TableTemplate` as the parent schema definition
- `TemplateColumn` as ordered typed column metadata
- Template CRUD and CSV scaffold export
- `pandas` already installed and available
- A file reader utility for CSV and Excel input

The project does not yet have:

- Persisted uploaded datasets
- Per-row or per-cell validation tracking
- Report definitions
- A reporting query engine
- Calculated fields
- Export flows for report outputs

## Target Architecture

The reporting feature should evolve the app into this data flow:

`TableTemplate -> Dataset -> DatasetImport -> DatasetRow -> DatasetCellIssue -> Report -> ReportWidget`

Optional semantic layer:

`CalculatedField`

This keeps `TableTemplate` as the schema contract and builds ingestion and reporting around it.

## Domain Model

### 1. Dataset

Represents a logical collection of uploaded tabular data tied to one template.

Suggested fields:

- `owner`
- `template`
- `name`
- `status`
- `row_count`
- `invalid_row_count`
- `last_imported_at`
- `created_at`
- `updated_at`

Suggested enums:

- `status`
  - `empty`
  - `ready`
  - `importing`
  - `failed`

Notes:

- One dataset belongs to one template
- Reports should be tied to a dataset, not just a template
- Dataset names should likely be unique per owner and template

### 2. DatasetImport

Represents one upload event into a dataset. Needed for append/replace tracking and auditability.

Suggested fields:

- `dataset`
- `source_filename`
- `source_file`
- `mode`
- `status`
- `total_rows`
- `inserted_rows`
- `invalid_rows`
- `extra_columns_json`
- `missing_columns_json`
- `header_mapping_json`
- `created_at`

Suggested enums:

- `mode`
  - `replace`
  - `append`
- `status`
  - `pending`
  - `processing`
  - `completed`
  - `failed`

Notes:

- `replace` deletes old rows for the dataset before saving the new import
- `append` keeps old rows and adds the new rows
- This model is the right place to preserve mapping choices and import summary details

### 3. DatasetRow

Represents one imported row stored as raw structured data.

Suggested fields:

- `dataset`
- `dataset_import`
- `row_index`
- `data_json`
- `is_valid`
- `issue_count`
- `created_at`

Notes:

- Store raw row values in `data_json` in v1
- Do not over-normalize per cell into a separate storage structure yet
- `data_json` keys should be based on stable internal field references, not display labels

### 4. DatasetCellIssue

Represents validation issues found in a specific row for a specific template column.

Suggested fields:

- `dataset_row`
- `template_column`
- `raw_value`
- `issue_code`
- `message`

Suggested issue codes:

- `missing_column`
- `missing_value`
- `invalid_integer`
- `invalid_float`
- `invalid_date`
- `invalid_boolean`
- `invalid_email`
- `invalid_url`
- `unmapped_source_column`

Notes:

- Rows are still stored even if they have issues
- Widgets should later decide whether invalid values are excluded from a calculation

### 5. CalculatedField

Represents reusable formulas at the dataset semantic layer.

Suggested fields:

- `dataset`
- `name`
- `formula`
- `data_type`
- `is_valid`
- `error_message`
- `sort_order`
- `created_at`
- `updated_at`

Notes:

- Calculated fields should belong to the dataset, not only the report
- Reports and widgets can then reuse them consistently
- Formula expressions should reference stable field IDs internally

### 6. Report

Represents a saved report definition tied to a specific dataset.

Suggested fields:

- `owner`
- `dataset`
- `name`
- `description`
- `layout_json`
- `created_at`
- `updated_at`

Notes:

- `layout_json` should remain minimal in v1 because the first builder is structured, not drag-and-drop
- Layout becomes more important when the visual editor arrives later

### 7. ReportWidget

Represents one chart or table inside a report.

Suggested fields:

- `report`
- `title`
- `widget_type`
- `config_json`
- `layout_x`
- `layout_y`
- `layout_w`
- `layout_h`
- `sort_order`
- `created_at`
- `updated_at`

Suggested widget types for v1:

- `table`
- `bar`
- `pie`
- `scatter`
- `histogram`

Notes:

- Store dimensions, metrics, and widget-specific settings in `config_json` in v1
- This avoids premature schema complexity

### 8. ReportFilter

Represents report-level filters that apply to widgets by default.

Suggested fields:

- `report`
- `field_kind`
- `field_ref`
- `operator`
- `value_json`
- `sort_order`

Suggested `field_kind`:

- `template_column`
- `calculated_field`

Notes:

- `field_ref` should store the stable database ID of the referenced field
- `value_json` should support scalar, list, or range values

## JSON Contracts

### DatasetRow.data_json

For v1, store data by stable template column ID as strings or `null`.

Example:

```json
{
  "12": "Alice",
  "13": "1200.50",
  "14": "2026-04-01",
  "15": null
}
```

This gives stable references even if a column name changes later.

### DatasetImport.header_mapping_json

Example:

```json
{
  "Customer Name": 12,
  "Total Spent": 13,
  "Purchase Date": 14
}
```

The key is the uploaded file header. The value is the target `TemplateColumn.id`.

### ReportWidget.config_json

Recommended shape:

```json
{
  "dimensions": [
    {
      "field_kind": "template_column",
      "field_ref": 12,
      "group_by": "raw"
    }
  ],
  "metrics": [
    {
      "field_kind": "template_column",
      "field_ref": 13,
      "aggregation": "sum",
      "label": "Total Spent"
    }
  ],
  "filters": [
    {
      "field_kind": "template_column",
      "field_ref": 14,
      "operator": "between",
      "value": ["2026-01-01", "2026-03-31"]
    }
  ],
  "sort": [
    {
      "target": "metric:0",
      "direction": "desc"
    }
  ]
}
```

## Validation Rules

### Template Column Data Types

Validation rules should be driven by `TemplateColumn.data_type`:

- `text`
  - accept any value
- `integer`
  - parseable integer required
- `float`
  - parseable decimal required
- `date`
  - parseable supported date required
- `boolean`
  - accept canonical values such as `true`, `false`, `yes`, `no`, `1`, `0`
- `email`
  - valid email format required
- `url`
  - valid URL format required

### Import Decisions

- Extra uploaded columns are flagged and ignored
- Missing mapped template columns become `null` in `data_json`
- Missing values generate issues but do not block import
- Rows with any issue are still saved

### Reporting Rules by Type

Allowed operations should be validated per field type.

#### `text`

- group by
- count
- distinct count
- equals
- contains
- in-list

#### `integer` and `float`

- sum
- avg
- min
- max
- count
- histogram bucket support
- numeric range filters
- scatter axes

#### `date`

- group by day
- group by week
- group by month
- group by year
- before
- after
- between
- min
- max

#### `boolean`

- group by
- count
- equals true or false

#### `email` and `url`

- treat as text in v1

## Import Workflow

The upload workflow should be implemented in these stages:

1. User chooses a template
2. User uploads CSV or Excel file
3. System reads file headers
4. System suggests header mapping based on exact or close matches
5. User adjusts mapping manually if needed
6. User chooses import mode
   - `replace`
   - `append`
7. Import executor validates each row and cell
8. Import summary is shown
9. Dataset detail page shows row and issue counts

### Replace Mode

- Remove prior `DatasetRow` records for the dataset
- Preserve the dataset record itself
- Preserve report definitions
- Create a new `DatasetImport` record
- Save the newly imported rows

### Append Mode

- Keep prior dataset rows
- Create a new `DatasetImport` record
- Save new rows in addition to existing rows

## Calculated Fields

Calculated fields should be introduced after ingestion and basic reporting are stable.

### Scope

- Belong to the dataset semantic layer
- Reusable across multiple reports and widgets
- Referenced internally by stable IDs

### Formula Support for v1

Allowed expression features:

- `+`
- `-`
- `*`
- `/`
- `%`
- parentheses
- `IF`
- `ROUND`
- `ABS`
- `COALESCE`

Notes:

- Do not allow arbitrary Python evaluation
- Formula parsing and execution must be sandboxed and explicit
- Formula references should resolve against template column IDs and calculated field IDs

### Example

User-facing formula:

```text
profit = revenue - cost
```

Internal representation should resolve `revenue` and `cost` to stable field references.

## Report Builder UX

The first version should use a structured builder instead of a drag-and-drop canvas.

### Report Builder Steps

1. Select dataset
2. Create report metadata
3. Add widget
4. Choose widget type
5. Choose dimensions
6. Choose metrics
7. Choose filters
8. Preview results
9. Save widget

### Widget Types for v1

- table
- bar
- pie
- scatter
- histogram

### Future Phase

Once the structured builder is stable:

- add drag-and-drop widget layout
- improve `layout_json`
- build PowerBI-style report canvas editing

## Query Engine Design

Create a service-layer query engine. Do not place report execution logic inside models or views.

Recommended service modules:

- `dashboard/services/report_fields.py`
- `dashboard/services/report_validation.py`
- `dashboard/services/report_query.py`

Responsibilities:

- resolve field references
- enforce type-specific reporting rules
- apply report and widget filters
- cast values according to template data types
- exclude invalid values when required by an aggregation
- compute calculated fields
- group and aggregate result sets
- return data structures ready for table and chart rendering
- return warnings about excluded invalid rows

### Execution Strategy

For v1, using `pandas` in the reporting execution layer is acceptable because:

- the dependency already exists
- uploaded data is tabular
- group-by and aggregation use cases are straightforward
- chart outputs map naturally to tabular aggregates

If scale increases later, execution can move toward normalized analytical storage or database-side aggregation.

## Export Strategy

Export should be delivered after query execution is stable.

### CSV

First export target.

- export widget result tables
- export report summary tables

### Excel

Second export target.

- export one workbook per report
- use one sheet per widget or report section

### PDF

Last export target.

- render a print-friendly HTML report first
- convert stable HTML output into PDF

PDF generation should come after layout and chart rendering are reliable.

## Recommended Django App Structure

Add reporting code gradually inside the existing `dashboard` app unless the scope becomes large enough to split later.

Suggested modules:

- `dashboard/models.py`
  - add new models initially here
- `dashboard/forms.py`
  - upload forms, mapping forms, report builder forms
- `dashboard/views.py`
  - dataset and report views
- `dashboard/services/import_readers.py`
- `dashboard/services/import_mapping.py`
- `dashboard/services/import_validation.py`
- `dashboard/services/import_executor.py`
- `dashboard/services/report_fields.py`
- `dashboard/services/report_validation.py`
- `dashboard/services/report_query.py`
- `dashboard/services/report_exports.py`

If the file grows too much, reporting can later be moved into a dedicated app.

## Suggested URL Surface

Example routes:

- `/datasets/`
- `/datasets/create/`
- `/datasets/<pk>/`
- `/datasets/<pk>/upload/`
- `/datasets/<pk>/imports/<import_pk>/`
- `/reports/`
- `/reports/create/`
- `/reports/<pk>/`
- `/reports/<pk>/builder/`
- `/reports/<pk>/export/csv/`
- `/reports/<pk>/export/excel/`
- `/reports/<pk>/export/pdf/`

## Migration Sequence

Implement in this order:

1. Add `Dataset`
2. Add `DatasetImport`
3. Add `DatasetRow`
4. Add `DatasetCellIssue`
5. Add dataset upload and import UI
6. Add import services and validation tests
7. Add `Report`
8. Add `ReportWidget`
9. Add `ReportFilter`
10. Add report builder UI
11. Add query engine services
12. Add exports
13. Add `CalculatedField`
14. Add visual editor later

## Testing Strategy

The feature should ship with tests for:

- import with exact header match
- import with manual header mapping
- import with extra columns
- import with missing template columns
- invalid integer, float, date, boolean, email, and URL handling
- row persistence even when issues exist
- append mode
- replace mode
- report access isolation by owner
- report validation by field type
- group by plus sum
- scatter, histogram, and pie validation
- calculated field parsing and evaluation
- CSV export
- Excel export
- PDF export once implemented

## Phase Breakdown

### Phase 1

Schema and ingestion foundation:

- `Dataset`
- `DatasetImport`
- `DatasetRow`
- `DatasetCellIssue`
- upload flow
- mapping flow
- import executor

### Phase 2

Basic reporting:

- `Report`
- `ReportWidget`
- `ReportFilter`
- structured report builder
- table, bar, pie, scatter, histogram
- result previews

### Phase 3

Exports:

- CSV
- Excel
- PDF

### Phase 4

Semantic enhancements:

- `CalculatedField`
- richer formula support
- better warnings and result introspection

### Phase 5

Visual design improvements:

- canvas editor
- widget layout drag-and-drop
- richer dashboard composition

## Final Recommendation

Do not begin with drag-and-drop report design or advanced formula support. The first milestone should be a stable ingestion layer plus structured report builder over one dataset tied to one template.

The recommended first deliverable is:

1. upload a file against a template
2. map headers
3. save dataset rows and issues
4. create a report with one widget
5. group and aggregate data
6. preview results
7. export to CSV

Once that works cleanly, the rest of the roadmap can build on it without reworking the foundation.
