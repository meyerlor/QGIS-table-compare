# Table Compare - Visual Diff Tool for QGIS

## Description

Table Compare is a powerful QGIS plugin that enables visual comparison of two vector layers or tables with similar structures. Perfect for version control, data auditing, and change detection workflows, this plugin highlights differences between datasets with intuitive color coding and detailed change tracking.

![Plugin Interface](Screenshots/Screen_1.jpg)

## Key Features

### Visual Difference Detection
- **Color-coded comparison**: Added (green), Deleted (red), Modified (yellow), Unchanged (white)
- **Field-level change highlighting**: Individual changed fields are highlighted with arrows showing "old → new" values
- **Smart comparison logic**: Handles different data types, floating-point precision, and null values

### Flexible Filtering Options
- **Status filters**: Show/hide Added, Deleted, Modified, or Unchanged features
- **Column selection**: Choose which fields to consider when determining modifications (exclude auto-generated fields like FID, timestamps)
- **Dynamic row numbering**: Row numbers automatically update when filtering

### Change Management
- **Accept/Reject workflow**: Mark individual changes or entire features as accepted or rejected
- **Bulk operations**: Accept or reject all changes at once
- **Visual feedback**: Accepted changes show in light green, rejected in light red

### Data Export
- **CSV export**: Export comparison results with decision status
- **Clean data**: Exported values reflect accept/reject decisions (old values for rejected, new values for accepted)
- **Filtered export**: Only exports visible rows based on current filters

### Advanced Functionality
- **Custom join fields**: Select which field to use for matching records between tables
- **Sortable results**: Click column headers to sort by any field
- **Multi-row selection**: Select multiple rows for batch accept/reject operations
- **Intelligent defaults**: Automatically excludes common system fields (fid, id, timestamps) from modification detection

## Use Cases

### Version Control & Data Auditing
- Compare different versions of the same dataset
- Track changes made by different team members
- Audit data modifications over time

### Quality Assurance
- Validate data imports and exports
- Check differences between original and processed datasets
- Ensure data integrity during migrations

### Collaborative Workflows
- Review changes before applying updates
- Coordinate data edits between team members
- Document approved vs. rejected modifications

### Data Synchronization
- Identify differences between master and working copies
- Merge changes from multiple data sources
- Maintain consistency across distributed datasets

## How It Works

1. **Select Tables**: Choose your "old" (reference) and "new" (comparison) vector layers
2. **Configure Join Field**: Select the field used to match records between tables
3. **Filter Columns**: Optionally exclude fields that shouldn't affect modification status
4. **Compare**: View results in an intuitive table with color-coded differences
5. **Review Changes**: Use filters to focus on specific types of changes
6. **Make Decisions**: Accept or reject changes as needed
7. **Export Results**: Save your comparison results and decisions to CSV

## Technical Requirements

- QGIS 3.0 or higher
- Vector layers with matching field structures
- Common unique identifier field between layers

## Perfect For

- GIS analysts and data managers
- Quality assurance teams
- Data migration projects
- Collaborative mapping projects
- Organizations requiring change documentation and approval workflows
