# table_compare_plugin.py
import os
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt, QDate, QDateTime
from qgis.PyQt.QtGui import QIcon, QColor
from qgis.PyQt.QtWidgets import (QAction, QDialog, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, 
                                QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox, 
                                QGroupBox, QFileDialog, QMessageBox, QAbstractItemView)
from qgis.core import QgsProject, QgsVectorLayer, QgsFeature
import qgis.utils
import csv

class TableComparePlugin:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        
        # Initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'TableCompare_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        self.actions = []
        self.menu = self.tr(u'&Table Compare')
        self.first_start = None

    def tr(self, message):
        return QCoreApplication.translate('TableComparePlugin', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)
        return action

    def initGui(self):
        icon_path = ':/plugins/table_compare/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Compare Tables'),
            callback=self.run,
            parent=self.iface.mainWindow())

        self.first_start = True

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Table Compare'),
                action)
            self.iface.removeToolBarIcon(action)

    def run(self):
        if self.first_start == True:
            self.first_start = False
            self.dlg = TableCompareDialog()

        self.dlg.show()
        result = self.dlg.exec_()


class TableCompareDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Table Comparison Tool")
        self.setMinimumSize(1000, 700)
        self.setup_ui()
        self.populate_layer_combos()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Layer selection
        selection_layout = QHBoxLayout()
        
        selection_layout.addWidget(QLabel("Old Table:"))
        self.old_table_combo = QComboBox()
        selection_layout.addWidget(self.old_table_combo)
        
        selection_layout.addWidget(QLabel("New Table:"))
        self.new_table_combo = QComboBox()
        selection_layout.addWidget(self.new_table_combo)
        
        selection_layout.addWidget(QLabel("Join Field:"))
        self.join_field_combo = QComboBox()
        self.join_field_combo.setMinimumWidth(120)
        selection_layout.addWidget(self.join_field_combo)
        
        self.refresh_button = QPushButton("Refresh Layers")
        self.refresh_button.clicked.connect(self.populate_layer_combos)
        selection_layout.addWidget(self.refresh_button)
        
        self.compare_button = QPushButton("Compare Tables")
        self.compare_button.clicked.connect(self.compare_tables)
        selection_layout.addWidget(self.compare_button)
        
        layout.addLayout(selection_layout)
        
        # Color legend
        legend_layout = QHBoxLayout()
        legend_layout.addWidget(QLabel("Legend:"))
        
        # Create colored legend items
        added_label = QLabel("Added")
        added_label.setStyleSheet("background-color: rgb(144, 238, 144); padding: 2px 8px; border: 1px solid gray;")
        legend_layout.addWidget(added_label)
        
        deleted_label = QLabel("Deleted")
        deleted_label.setStyleSheet("background-color: rgb(255, 99, 99); padding: 2px 8px; border: 1px solid gray;")
        legend_layout.addWidget(deleted_label)
        
        modified_label = QLabel("Modified")
        modified_label.setStyleSheet("background-color: rgb(255, 255, 150); padding: 2px 8px; border: 1px solid gray;")
        legend_layout.addWidget(modified_label)
        
        unchanged_label = QLabel("Unchanged")
        unchanged_label.setStyleSheet("background-color: rgb(255, 255, 255); padding: 2px 8px; border: 1px solid gray;")
        legend_layout.addWidget(unchanged_label)
        
        changed_field_label = QLabel("Changed Field")
        changed_field_label.setStyleSheet("background-color: rgb(255, 150, 150); padding: 2px 8px; border: 1px solid gray;")
        legend_layout.addWidget(changed_field_label)
        
        legend_layout.addStretch()  # Push legend items to the left
        layout.addLayout(legend_layout)
        
        # Filter options
        filter_group = QGroupBox("Filter Results")
        filter_layout = QHBoxLayout()
        
        self.filter_added = QCheckBox("Added")
        self.filter_added.setChecked(True)
        self.filter_added.stateChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.filter_added)
        
        self.filter_deleted = QCheckBox("Deleted")
        self.filter_deleted.setChecked(True)
        self.filter_deleted.stateChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.filter_deleted)
        
        self.filter_modified = QCheckBox("Modified")
        self.filter_modified.setChecked(True)
        self.filter_modified.stateChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.filter_modified)
        
        self.filter_unchanged = QCheckBox("Unchanged")
        self.filter_unchanged.setChecked(True)
        self.filter_unchanged.stateChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.filter_unchanged)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # Accept/Reject controls
        actions_group = QGroupBox("Actions")
        actions_layout = QHBoxLayout()
        
        self.accept_selected_btn = QPushButton("Accept Selected Changes")
        self.accept_selected_btn.clicked.connect(self.accept_selected_changes)
        actions_layout.addWidget(self.accept_selected_btn)
        
        self.reject_selected_btn = QPushButton("Reject Selected Changes")
        self.reject_selected_btn.clicked.connect(self.reject_selected_changes)
        actions_layout.addWidget(self.reject_selected_btn)
        
        self.accept_all_btn = QPushButton("Accept All")
        self.accept_all_btn.clicked.connect(self.accept_all_changes)
        actions_layout.addWidget(self.accept_all_btn)
        
        self.reject_all_btn = QPushButton("Reject All")
        self.reject_all_btn.clicked.connect(self.reject_all_changes)
        actions_layout.addWidget(self.reject_all_btn)
        
        self.export_btn = QPushButton("Export Results")
        self.export_btn.clicked.connect(self.export_results)
        actions_layout.addWidget(self.export_btn)
        
        self.column_filter_btn = QPushButton("Select Columns to Check")
        self.column_filter_btn.clicked.connect(self.select_columns_to_check)
        actions_layout.addWidget(self.column_filter_btn)
        
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setSortingEnabled(True)  # Enable sorting
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectRows)  # Select entire rows
        self.results_table.setSelectionMode(QAbstractItemView.MultiSelection)  # Allow multiple selection
        layout.addWidget(self.results_table)
        
        # Connect sorting signal to update row numbers after sort
        self.results_table.horizontalHeader().sectionClicked.connect(self.on_column_sort)
        
        # Connect layer selection to update join field options
        self.old_table_combo.currentTextChanged.connect(self.update_join_fields)
        self.new_table_combo.currentTextChanged.connect(self.update_join_fields)
        
        self.setLayout(layout)
        
        # Store original data for filtering
        self.all_rows_data = []
        self.comparison_data = {}  # Store comparison results for accept/reject functionality
        self.original_row_order = []  # Store original row data for sorting
        self.columns_to_check = []  # Store which columns should be checked for modifications

    def populate_layer_combos(self):
        """Populate combo boxes with available vector layers"""
        self.old_table_combo.clear()
        self.new_table_combo.clear()
        
        layers = QgsProject.instance().mapLayers().values()
        vector_layers = [layer for layer in layers if isinstance(layer, QgsVectorLayer)]
        
        for layer in vector_layers:
            self.old_table_combo.addItem(layer.name(), layer)
            self.new_table_combo.addItem(layer.name(), layer)
        
        # Update join fields after populating layers
        self.update_join_fields()

    def update_join_fields(self):
        """Update join field options based on selected layers"""
        self.join_field_combo.clear()
        
        old_layer = self.old_table_combo.currentData()
        new_layer = self.new_table_combo.currentData()
        
        if old_layer and new_layer:
            # Get common fields between both layers
            old_fields = set(field.name() for field in old_layer.fields())
            new_fields = set(field.name() for field in new_layer.fields())
            common_fields = old_fields.intersection(new_fields)
            
            for field in sorted(common_fields):
                self.join_field_combo.addItem(field)

    def apply_filters(self):
        """Apply filters to hide/show rows based on status and update dynamic row numbering in headers"""
        if not hasattr(self, 'all_rows_data') or not self.all_rows_data:
            return
            
        show_added = self.filter_added.isChecked()
        show_deleted = self.filter_deleted.isChecked()
        show_modified = self.filter_modified.isChecked()
        show_unchanged = self.filter_unchanged.isChecked()
        
        for row in range(self.results_table.rowCount()):
            status_item = self.results_table.item(row, 0)  # Status is back to column 0
            if status_item:
                status = status_item.text()
                should_show = (
                    (status == "Added" and show_added) or
                    (status == "Deleted" and show_deleted) or
                    (status == "Modified" and show_modified) or
                    (status == "Unchanged" and show_unchanged)
                )
                
                self.results_table.setRowHidden(row, not should_show)
        
        # Update dynamic row numbering for visible rows
        self.update_dynamic_row_numbers()

    def format_value(self, value):
        """Format values for display, handling special types like dates"""
        if isinstance(value, QDate):
            return value.toString("yyyy-MM-dd")
        elif isinstance(value, QDateTime):
            return value.toString("yyyy-MM-dd hh:mm:ss")
        elif value is None:
            return ""
        else:
            return str(value)
    
    def values_equal(self, val1, val2):
        """Compare two values for equality, handling different data types"""
        # Handle None values
        if val1 is None and val2 is None:
            return True
        if val1 is None or val2 is None:
            return False
        
        # Convert to strings for comparison to handle type differences
        str1 = str(val1).strip()
        str2 = str(val2).strip()
        
        # Handle numeric comparison
        try:
            float1 = float(str1)
            float2 = float(str2)
            # Compare with small tolerance for floating point precision
            return abs(float1 - float2) < 1e-10
        except (ValueError, TypeError):
            # Not numeric, compare as strings
            return str1 == str2

    def accept_selected_changes(self):
        """Accept selected changes"""
        selected_rows = set()
        for item in self.results_table.selectedItems():
            selected_rows.add(item.row())
        
        for row in selected_rows:
            status_item = self.results_table.item(row, 0)  # Status is back to column 0
            if status_item and status_item.text() in ["Modified", "Added"]:
                # Mark as accepted (change background to light green)
                for col in range(self.results_table.columnCount()):
                    item = self.results_table.item(row, col)
                    if item:
                        item.setBackground(QColor(200, 255, 200))  # Light green for accepted

    def reject_selected_changes(self):
        """Reject selected changes"""
        selected_rows = set()
        for item in self.results_table.selectedItems():
            selected_rows.add(item.row())
        
        for row in selected_rows:
            status_item = self.results_table.item(row, 0)  # Status is back to column 0
            if status_item and status_item.text() in ["Modified", "Added"]:
                # Mark as rejected (change background to light red)
                for col in range(self.results_table.columnCount()):
                    item = self.results_table.item(row, col)
                    if item:
                        item.setBackground(QColor(255, 200, 200))  # Light red for rejected

    def accept_all_changes(self):
        """Accept all changes"""
        for row in range(self.results_table.rowCount()):
            status_item = self.results_table.item(row, 0)  # Status is back to column 0
            if status_item and status_item.text() in ["Modified", "Added"]:
                for col in range(self.results_table.columnCount()):
                    item = self.results_table.item(row, col)
                    if item:
                        item.setBackground(QColor(200, 255, 200))  # Light green for accepted

    def reject_all_changes(self):
        """Reject all changes"""
        for row in range(self.results_table.rowCount()):
            status_item = self.results_table.item(row, 0)  # Status is back to column 0
            if status_item and status_item.text() in ["Modified", "Added"]:
                for col in range(self.results_table.columnCount()):
                    item = self.results_table.item(row, col)
                    if item:
                        item.setBackground(QColor(255, 200, 200))  # Light red for rejected

    def export_results(self):
        """Export comparison results to CSV"""
        if self.results_table.rowCount() == 0:
            QMessageBox.warning(self, "Warning", "No data to export!")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "Export Comparison Results", 
            "comparison_results.csv", 
            "CSV files (*.csv)"
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Write headers (all columns)
                    headers = []
                    for col in range(self.results_table.columnCount()):
                        header_item = self.results_table.horizontalHeaderItem(col)
                        headers.append(header_item.text() if header_item else f"Column_{col}")
                    
                    # Add decision column
                    headers.append("Decision")
                    writer.writerow(headers)
                    
                    # Write data
                    for row in range(self.results_table.rowCount()):
                        if self.results_table.isRowHidden(row):
                            continue  # Skip hidden rows
                            
                        row_data = []
                        decision = "Pending"
                        
                        # Get the status for this row (back to column 0)
                        status_item = self.results_table.item(row, 0)
                        status = status_item.text() if status_item else ""
                        
                        # Determine decision based on background color of status column
                        if status_item:
                            bg_color = status_item.background().color()
                            if bg_color == QColor(200, 255, 200):
                                decision = "Accepted"
                            elif bg_color == QColor(255, 200, 200):
                                decision = "Rejected"
                        
                        # Export all columns
                        for col in range(self.results_table.columnCount()):
                            item = self.results_table.item(row, col)
                            if item:
                                text = item.text()
                                
                                # If this contains an arrow (indicating a change), extract only the appropriate value
                                if " → " in text:
                                    if decision == "Rejected":
                                        # For rejected changes, export the old value (before arrow)
                                        clean_text = text.split(" → ")[0]
                                    else:
                                        # For accepted or pending changes, export the new value (after arrow)
                                        clean_text = text.split(" → ")[1]
                                else:
                                    # No change, use as is
                                    clean_text = text
                                
                                row_data.append(clean_text)
                            else:
                                row_data.append("")
                        
                        row_data.append(decision)
                        writer.writerow(row_data)
                
                QMessageBox.information(self, "Success", f"Results exported to {filename}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export: {str(e)}")

    def select_columns_to_check(self):
        """Allow user to select which columns should be checked for modifications"""
        old_layer = self.old_table_combo.currentData()
        if not old_layer:
            QMessageBox.warning(self, "Warning", "Please select the old table first!")
            return
        
        # Get all field names
        all_fields = [field.name() for field in old_layer.fields()]
        
        if not all_fields:
            QMessageBox.warning(self, "Warning", "No fields found in selected table!")
            return
        
        from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QPushButton, QLabel, QScrollArea, QWidget
        
        # Create dialog for column selection
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Columns to Check for Modifications")
        dialog.setMinimumSize(400, 300)
        
        layout = QVBoxLayout()
        
        # Add instruction label
        instruction = QLabel("Select which columns should be checked when determining if a feature is 'Modified'.\nUnchecked columns will be ignored (e.g., fid, timestamps).")
        instruction.setWordWrap(True)
        layout.addWidget(instruction)
        
        # Create scroll area for checkboxes
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        # Create checkboxes for each field
        checkboxes = {}
        for field in all_fields:
            checkbox = QCheckBox(field)
            # Default: check all columns except common auto-generated ones
            if field.lower() not in ['fid', 'id', 'objectid', 'gid', 'created_date', 'modified_date', 'timestamp']:
                checkbox.setChecked(True)
            checkboxes[field] = checkbox
            scroll_layout.addWidget(checkbox)
        
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Add buttons
        button_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(lambda: [cb.setChecked(True) for cb in checkboxes.values()])
        button_layout.addWidget(select_all_btn)
        
        select_none_btn = QPushButton("Select None")
        select_none_btn.clicked.connect(lambda: [cb.setChecked(False) for cb in checkboxes.values()])
        button_layout.addWidget(select_none_btn)
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        
        # Show dialog and get result
        if dialog.exec_() == QDialog.Accepted:
            # Store selected columns
            self.columns_to_check = [field for field, checkbox in checkboxes.items() if checkbox.isChecked()]
            
            # Automatically re-run comparison if we have data
            if self.results_table.rowCount() > 0:
                QMessageBox.information(
                    self, 
                    "Columns Updated", 
                    f"Selected {len(self.columns_to_check)} columns to check for modifications.\n"
                    f"Comparison results updated automatically."
                )
                # Re-run the comparison with new settings
                self.compare_tables()
            else:
                QMessageBox.information(
                    self, 
                    "Columns Updated", 
                    f"Selected {len(self.columns_to_check)} columns to check for modifications.\n"
                    f"Click 'Compare Tables' to see results."
                )

    def on_column_sort(self):
        """Called when a column header is clicked for sorting - update row numbers after sort"""
        # Use a short delay to ensure the sort operation completes first
        from qgis.PyQt.QtCore import QTimer
        QTimer.singleShot(10, self.update_dynamic_row_numbers)

    def update_dynamic_row_numbers(self):
        """Update the dynamic row numbering in vertical headers for visible rows"""
        visible_row_count = 0
        
        for row in range(self.results_table.rowCount()):
            if not self.results_table.isRowHidden(row):
                visible_row_count += 1
                self.results_table.setVerticalHeaderItem(row, QTableWidgetItem(str(visible_row_count)))

    def compare_tables(self):
        """Main comparison logic"""
        old_layer = self.old_table_combo.currentData()
        new_layer = self.new_table_combo.currentData()
        
        if not old_layer or not new_layer:
            return
        
        # Clear previous results completely
        self.results_table.setRowCount(0)
        self.results_table.setColumnCount(0)
        self.all_rows_data = []
        self.comparison_data = {}
            
        # Get field names (assuming same structure)
        fields = [field.name() for field in old_layer.fields()]
        
        # If no columns selected for checking, use all fields
        if not self.columns_to_check:
            self.columns_to_check = [f for f in fields if f.lower() not in ['fid', 'id', 'objectid', 'gid', 'created_date', 'modified_date', 'timestamp']]
        
        # Get selected join field
        join_field = self.join_field_combo.currentText()
        if not join_field:
            # Fallback to first field if none selected
            join_field = fields[0] if fields else None
        
        if not join_field:
            return
        
        # Create dictionaries for comparison
        old_features = {}
        new_features = {}
        
        # Populate old features
        for feature in old_layer.getFeatures():
            feature_id = feature[join_field]
            old_features[feature_id] = {field: feature[field] for field in fields}
        
        # Populate new features
        for feature in new_layer.getFeatures():
            feature_id = feature[join_field]
            new_features[feature_id] = {field: feature[field] for field in fields}
        
        self.display_comparison_results(old_features, new_features, fields)

    def display_comparison_results(self, old_features, new_features, fields):
        """Display comparison results in the table widget"""
        all_ids = set(old_features.keys()) | set(new_features.keys())
        
        # Setup table
        self.results_table.setRowCount(len(all_ids))
        self.results_table.setColumnCount(len(fields) + 1)  # +1 for status column only
        
        headers = ["Status"] + fields
        self.results_table.setHorizontalHeaderLabels(headers)
        
        # Clear previous data
        self.all_rows_data = []
        self.comparison_data = {}  # Reset comparison data
        
        # Colors for different states - more distinguishable colors
        added_color = QColor(144, 238, 144)    # Light green
        deleted_color = QColor(255, 99, 99)    # Bright red (more distinct)
        modified_color = QColor(255, 255, 150) # Bright yellow (more distinct)
        unchanged_color = QColor(255, 255, 255) # White
        
        row = 0
        for feature_id in sorted(all_ids):
            status = ""
            row_color = unchanged_color
            
            if feature_id in old_features and feature_id in new_features:
                # Feature exists in both - check if modified
                old_data = old_features[feature_id]
                new_data = new_features[feature_id]
                
                # Check if any field is actually different - only check selected columns
                is_modified = False
                for field in self.columns_to_check:
                    if field in old_data and field in new_data:
                        if not self.values_equal(old_data.get(field), new_data.get(field)):
                            is_modified = True
                            break
                
                if is_modified:
                    status = "Modified"
                    row_color = modified_color
                else:
                    status = "Unchanged"
                    row_color = unchanged_color
                
                # Use new data for display
                data = new_data
                
            elif feature_id in new_features:
                # Added feature
                status = "Added"
                row_color = added_color
                data = new_features[feature_id]
                
            else:
                # Deleted feature
                status = "Deleted"
                row_color = deleted_color
                data = old_features[feature_id]
            
            # Set row header (dynamic numbering)
            self.results_table.setVerticalHeaderItem(row, QTableWidgetItem(str(row + 1)))
            
            # Set status
            status_item = QTableWidgetItem(status)
            status_item.setBackground(row_color)
            self.results_table.setItem(row, 0, status_item)
            
            # Set field values
            for col, field in enumerate(fields, 1):  # Start from column 1
                if status == "Modified" and feature_id in old_features and feature_id in new_features:
                    old_value = old_features[feature_id].get(field)
                    new_value = new_features[feature_id].get(field)
                    
                    # Only show arrows and highlighting for fields that are being checked
                    if field in self.columns_to_check and not self.values_equal(old_value, new_value):
                        # Show change: old -> new (only for fields we're checking)
                        display_text = f"{self.format_value(old_value)} → {self.format_value(new_value)}"
                        item = QTableWidgetItem(display_text)
                        item.setBackground(QColor(255, 150, 150))  # Darker red for changed fields
                    else:
                        # Either field not being checked OR no change - just show new value
                        item = QTableWidgetItem(self.format_value(new_value))
                        item.setBackground(row_color)  # Use row color
                else:
                    # Use appropriate value based on status
                    item = QTableWidgetItem(self.format_value(data.get(field, '')))
                    item.setBackground(row_color)  # Always apply row color
                
                self.results_table.setItem(row, col, item)
            
            # Store comparison data for this feature
            self.comparison_data[feature_id] = {
                'status': status,
                'old_data': old_features.get(feature_id, {}),
                'new_data': new_features.get(feature_id, {}),
                'row': row
            }
            
            row += 1
        
        # Store data for filtering
        self.all_rows_data = list(range(self.results_table.rowCount()))
        
        # Resize columns to content
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        
        # Apply current filters
        self.apply_filters()