# PrintSplitterAddon/PrintSplitterTaskPanel.py

import FreeCAD
import FreeCADGui
from PySide import QtGui, QtCore

# --- Necessary Imports ---
import Part
import math
from FreeCAD import Base # For Vector
import Draft # Potentially needed for upgrade/downgrade later if booleans fail often
# --- End of Imports ---

class PrintSplitterTaskPanel:
    """
    Defines the Task Panel UI and the core processing logic.
    """
    def __init__(self, selected_obj):
        self.obj_to_split = selected_obj
        self.dialog = None

        # --- UI Setup ---
        self.form = QtGui.QWidget()
        main_layout = QtGui.QVBoxLayout(self.form)

        # Title
        title_label = QtGui.QLabel("<b>Print Splitter Settings</b>")
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Printer Volume Group
        printer_group = QtGui.QGroupBox("Printer Build Volume (mm)")
        printer_layout = QtGui.QFormLayout(printer_group)
        self.printer_x_input = QtGui.QLineEdit("200.0")
        self.printer_x_input.setValidator(QtGui.QDoubleValidator(1.0, 10000.0, 2)) # Min 1mm
        printer_layout.addRow("Width (X):", self.printer_x_input)
        self.printer_y_input = QtGui.QLineEdit("200.0")
        self.printer_y_input.setValidator(QtGui.QDoubleValidator(1.0, 10000.0, 2))
        printer_layout.addRow("Depth (Y):", self.printer_y_input)
        self.printer_z_input = QtGui.QLineEdit("200.0")
        self.printer_z_input.setValidator(QtGui.QDoubleValidator(1.0, 10000.0, 2))
        printer_layout.addRow("Height (Z):", self.printer_z_input)
        main_layout.addWidget(printer_group)

        # Connector Options Group
        self.connector_group = QtGui.QGroupBox("Connector Options")
        self.connector_group.setCheckable(True) # Make group checkable
        self.connector_group.setChecked(True) # Enable by default
        connector_layout = QtGui.QFormLayout(self.connector_group)

        self.pin_diameter_input = QtGui.QLineEdit("5.0")
        self.pin_diameter_input.setValidator(QtGui.QDoubleValidator(0.5, 100.0, 2))
        connector_layout.addRow("Pin Diameter (mm):", self.pin_diameter_input)

        self.pin_height_input = QtGui.QLineEdit("4.0")
        self.pin_height_input.setValidator(QtGui.QDoubleValidator(0.5, 100.0, 2))
        connector_layout.addRow("Pin Height (mm):", self.pin_height_input)

        self.tolerance_input = QtGui.QLineEdit("0.3")
        self.tolerance_input.setValidator(QtGui.QDoubleValidator(0.0, 5.0, 2)) # Tolerance can be 0
        connector_layout.addRow("Tolerance (mm):", self.tolerance_input)
        connector_info = QtGui.QLabel("<i>Tolerance adds clearance around pin for hole. Hole Dia = Pin Dia + 2*Tol.</i>")
        connector_info.setWordWrap(True)
        connector_layout.addRow(connector_info)

        main_layout.addWidget(self.connector_group)

        # Process Button
        self.process_button = QtGui.QPushButton("Split Object")
        self.process_button.clicked.connect(self.process)
        main_layout.addWidget(self.process_button)

        main_layout.addStretch()
        self.form.setLayout(main_layout)
        # --- End of UI Setup ---

    def show(self):
        """ Muestra el panel de tareas """
        # La forma correcta es usar showDialog con la instancia del panel
        # Asegurándonos de que esta es la línea que se usa:
        FreeCADGui.Control.showDialog(self)

    def accept(self): return True # Dialog handled by button click
    def reject(self):
        FreeCADGui.Control.closeDialog(self.dialog)
        return True
    def close(self):
        if self.dialog: FreeCADGui.Control.closeDialog(self.dialog)

    # --- Helper Function: Find Matching Faces ---
    def find_matching_planar_faces(self, shape1, shape2, tolerance=1e-4):
        matching_face_indices = []
        if not shape1 or shape1.isNull() or not shape2 or shape2.isNull(): return []
        if not isinstance(shape1, Part.Shape) or not isinstance(shape2, Part.Shape): return []

        try: faces1, faces2 = shape1.Faces, shape2.Faces
        except: return []

        min_area = tolerance * tolerance * 10 # Ignore very small faces

        for i, f1 in enumerate(faces1):
            try:
                if f1.Surface.TypeId == "Part::GeomPlane" and f1.Area > min_area:
                    com1 = f1.CenterOfMass
                    try: normal1 = f1.normalAt(f1.Surface.parameter(com1)[0], f1.Surface.parameter(com1)[1])
                    except: continue

                    for j, f2 in enumerate(faces2):
                        try:
                            if f2.Surface.TypeId == "Part::GeomPlane" and f2.Area > min_area:
                                com2 = f2.CenterOfMass
                                if not f1.BoundBox.intersect(f2.BoundBox).isValid(): continue

                                distance = com1.distanceToPoint(com2)
                                if distance < tolerance:
                                    try: normal2 = f2.normalAt(f2.Surface.parameter(com2)[0], f2.Surface.parameter(com2)[1])
                                    except: continue

                                    dot_product = normal1.dot(normal2)
                                    # Check if normals are opposite (dot product close to -1)
                                    if abs(dot_product + 1.0) < tolerance:
                                        # --- DEBUG --- 
                                        # FreeCAD.Console.PrintMessage(f"      Found Potential Match: Face {i} (Area {f1.Area:.1f}) of Shape1 and Face {j} (Area {f2.Area:.1f}) of Shape2 at dist {distance:.4f}")
                                        # ------------- 
                                        matching_face_indices.append((i, j))
                        except: pass # Inner loop error
            except: pass # Outer loop error
        return matching_face_indices

    # --- Helper Function: Check if BBox Fits Printer ---
    def check_fit(self, piece_bbox, printer_dims):
        """ Checks if the piece_bbox fits within printer_dims in any axis-aligned orientation """
        px, py, pz = printer_dims
        bx, by, bz = piece_bbox.XLength, piece_bbox.YLength, piece_bbox.ZLength

        # Check all 6 permutations
        orientations = [
            (bx, by, bz), (bx, bz, by),
            (by, bx, bz), (by, bz, bx),
            (bz, bx, by), (bz, by, bx)
        ]

        for obx, oby, obz in orientations:
            if obx <= px + 1e-6 and oby <= py + 1e-6 and obz <= pz + 1e-6: # Add small tolerance for float issues
                return True # Fits in this orientation
        return False # Does not fit in any orientation


    # --- Main Processing Function ---
    def process(self):
        FreeCAD.ActiveDocument.openTransaction("Split and Add Connectors") # Start transaction
        piece_objects = [] # Keep track of created Part::Feature objects
        result_group = None # Group for results
        temp_cutter_obj = None # For temporary cutter features

        try:
            # --- Get Inputs ---
            printer_x = float(self.printer_x_input.text())
            printer_y = float(self.printer_y_input.text())
            printer_z = float(self.printer_z_input.text())
            printer_dims = (printer_x, printer_y, printer_z)

            add_connectors = self.connector_group.isChecked()
            pin_diameter = float(self.pin_diameter_input.text()) if add_connectors else 0
            pin_height = float(self.pin_height_input.text()) if add_connectors else 0
            tolerance = float(self.tolerance_input.text()) if add_connectors else 0

            if add_connectors and (pin_diameter <= 0 or pin_height <= 0):
                 raise ValueError("Pin diameter and height must be positive if adding connectors.")

            if not self.obj_to_split:
                raise ValueError("No object selected.")

            FreeCAD.Console.PrintMessage(f"Starting process for: {self.obj_to_split.Label}\n")
            FreeCAD.Console.PrintMessage(f"Printer Volume: X={printer_x:.2f}, Y={printer_y:.2f}, Z={printer_z:.2f}\n")
            if add_connectors:
                 FreeCAD.Console.PrintMessage(f"Connectors: Enabled (Dia={pin_diameter:.2f}, Height={pin_height:.2f}, Tol={tolerance:.2f})\n")
            else:
                 FreeCAD.Console.PrintMessage("Connectors: Disabled\n")


            # --- Get the initial shape ---
            initial_shape = self.obj_to_split.Shape
            shape_to_split = None # Initialize

            # --- Attempt to convert to solid ---
            FreeCAD.Console.PrintMessage("Attempting to ensure object is solid...\n")
            try:
                if isinstance(initial_shape, Part.Solid):
                    FreeCAD.Console.PrintMessage("  Object is already a solid.\n")
                    shape_to_split = initial_shape
                elif isinstance(initial_shape, Part.Compound):
                    FreeCAD.Console.PrintMessage("  Object is a Compound. Attempting to create solid via Shell(Faces) -> makeSolid()...\n")
                    try:
                        # Check if the compound has faces first
                        if initial_shape.Faces:
                            # 1. Try creating a single shell from all faces
                            temp_shell = Part.Shell(initial_shape.Faces)
                            if temp_shell and not temp_shell.isNull():
                                FreeCAD.Console.PrintMessage("    Intermediate shell created from faces.\n")
                                # 2. Try creating a solid from the shell using Part.makeSolid()
                                converted_solid = Part.makeSolid(temp_shell)
                                if converted_solid and isinstance(converted_solid, Part.Solid) and converted_solid.Volume > 1e-9:
                                    FreeCAD.Console.PrintMessage("    Conversion from Compound faces via shell successful.\n")
                                    shape_to_split = converted_solid
                                else:
                                    FreeCAD.Console.PrintWarning("    Part.makeSolid() failed on shell created from Compound faces. Proceeding with original Compound.\n")
                                    shape_to_split = initial_shape # Fallback
                            else:
                                FreeCAD.Console.PrintWarning("    Failed to create intermediate shell from Compound faces. Proceeding with original Compound.\n")
                                shape_to_split = initial_shape # Fallback
                        else:
                             FreeCAD.Console.PrintWarning("    Compound contains no faces to form a shell/solid from. Proceeding with original Compound.\n")
                             shape_to_split = initial_shape
                    except Exception as comp_conv_err:
                         FreeCAD.Console.PrintWarning(f"    Error during Compound conversion via faces/shell: {comp_conv_err}. Proceeding with original Compound.\n")
                         shape_to_split = initial_shape
                elif isinstance(initial_shape, Part.Shell):
                    FreeCAD.Console.PrintMessage("  Object is a Shell. Attempting conversion using Part.makeSolid()...\n")
                    try:
                        converted_solid = Part.makeSolid(initial_shape)
                        if converted_solid and isinstance(converted_solid, Part.Solid) and converted_solid.Volume > 1e-9:
                            FreeCAD.Console.PrintMessage("    Conversion from Shell successful.\n")
                            shape_to_split = converted_solid
                        else:
                            FreeCAD.Console.PrintWarning("    Part.makeSolid() failed or resulted in invalid/zero-volume solid. Proceeding with original Shell.\n")
                            shape_to_split = initial_shape # Fallback to original shell
                    except Exception as shell_conv_err:
                        FreeCAD.Console.PrintWarning(f"    Error during Shell Part.makeSolid() conversion: {shell_conv_err}. Proceeding with original Shell.\n")
                        shape_to_split = initial_shape
                else:
                    # Handle other types like Face, Wire etc. - Cannot convert directly here.
                    FreeCAD.Console.PrintWarning(f"  Object type ({type(initial_shape).__name__}) cannot be automatically converted to solid here. Proceeding with original shape.\n")
                    shape_to_split = initial_shape # Fallback

            except Exception as conv_err:
                FreeCAD.Console.PrintWarning(f"  Unexpected error during automatic solid conversion check: {conv_err}. Proceeding with original shape.\n")
                shape_to_split = initial_shape # Fallback to original

            # Ensure we have a shape to work with before proceeding
            if not shape_to_split or shape_to_split.isNull():
                 raise ValueError("Could not obtain a valid shape from the selected object after conversion attempt.")

            # --- Initial Splitting Checks (using the potentially converted shape) ---
            # shape_to_split = self.obj_to_split.Shape # This line is replaced by the logic above
            global_bbox = shape_to_split.BoundBox.transformed(self.obj_to_split.Placement.Matrix)
            needs_split_x = global_bbox.XLength > printer_x
            needs_split_y = global_bbox.YLength > printer_y
            needs_split_z = global_bbox.ZLength > printer_z

            if not (needs_split_x or needs_split_y or needs_split_z):
                # Check if it fits WITHOUT splitting
                 local_bbox = shape_to_split.BoundBox # Use local bbox for fitting check
                 if self.check_fit(local_bbox, printer_dims):
                     FreeCAD.Console.PrintWarning("Object already fits within the printer volume. No splitting needed.\n")
                     QtGui.QMessageBox.information(None, "Info", "The selected object already fits within the specified printer volume.")
                     FreeCAD.ActiveDocument.abortTransaction()
                     self.close()
                     return
                 else:
                      FreeCAD.Console.PrintWarning("Object bounding box exceeds printer volume in all orientations, even though individual dimensions might be smaller. Proceeding with split based on dimensions.\n")
                      # Fall through to splitting based on dimensions comparison

            # Calculate and Create Cutting TOOLS (Boxes instead of Planes)
            cutting_tool_shapes = []
            tool_buffer = max(global_bbox.XLength, global_bbox.YLength, global_bbox.ZLength) * 2 # Even larger buffer for boxes
            tool_thickness = 0.001 # Very small thickness for the cutting box

            # X Cuts - Create Boxes
            num_cuts_x = int(math.ceil(global_bbox.XLength / printer_x)) - 1 if needs_split_x else 0
            if num_cuts_x > 0:
                step_x = global_bbox.XLength / (num_cuts_x + 1)
                for i in range(1, num_cuts_x + 1):
                    pos_x = global_bbox.XMin + i * step_x
                    # Center the box on the cut plane, make it large in Y/Z, thin in X
                    center_vec = Base.Vector(pos_x, global_bbox.Center.y, global_bbox.Center.z)
                    box = Part.makeBox(tool_thickness, tool_buffer, tool_buffer, center_vec)
                    # Adjust position so the center is on the cut plane
                    box.translate(Base.Vector(-tool_thickness / 2, -tool_buffer / 2, -tool_buffer / 2))
                    cutting_tool_shapes.append(box)
            # Y Cuts - Create Boxes
            num_cuts_y = int(math.ceil(global_bbox.YLength / printer_y)) - 1 if needs_split_y else 0
            if num_cuts_y > 0:
                step_y = global_bbox.YLength / (num_cuts_y + 1)
                for i in range(1, num_cuts_y + 1):
                    pos_y = global_bbox.YMin + i * step_y
                    center_vec = Base.Vector(global_bbox.Center.x, pos_y, global_bbox.Center.z)
                    box = Part.makeBox(tool_buffer, tool_thickness, tool_buffer, center_vec)
                    box.translate(Base.Vector(-tool_buffer / 2, -tool_thickness / 2, -tool_buffer / 2))
                    cutting_tool_shapes.append(box)
            # Z Cuts - Create Boxes
            num_cuts_z = int(math.ceil(global_bbox.ZLength / printer_z)) - 1 if needs_split_z else 0
            if num_cuts_z > 0:
                step_z = global_bbox.ZLength / (num_cuts_z + 1)
                for i in range(1, num_cuts_z + 1):
                    pos_z = global_bbox.ZMin + i * step_z
                    center_vec = Base.Vector(global_bbox.Center.x, global_bbox.Center.y, pos_z)
                    box = Part.makeBox(tool_buffer, tool_buffer, tool_thickness, center_vec)
                    box.translate(Base.Vector(-tool_buffer / 2, -tool_buffer / 2, -tool_thickness / 2))
                    cutting_tool_shapes.append(box)

            if not cutting_tool_shapes:
                 raise ValueError("Object needs splitting based on orientation fit, but no cutting tools generated.")

            # Execute Split Operation using sequential Part.cut with boxes
            FreeCAD.Console.PrintMessage(f"Attempting splitting using Part.cut with {len(cutting_tool_shapes)} box tool(s)...\n")

            # Start with the original shape
            current_pieces = [shape_to_split]

            try:
                # Iterate through each calculated cutting tool shape (box)
                for i, tool_shape in enumerate(cutting_tool_shapes):
                    FreeCAD.Console.PrintMessage(f"  Applying cut with tool {i+1}...\n")
                    next_pieces = [] # Store results of cutting with this tool
                    for piece in current_pieces:
                        if piece.isNull() or not isinstance(piece, Part.Solid):
                            continue # Skip invalid pieces

                        # --- Add validity check before cutting ---
                        try:
                            piece.check() # Check if the piece is geometrically valid
                            # FreeCAD.Console.PrintMessage(f"    Piece valid before cut {i+1}. Volume: {piece.Volume:.2f}")
                        except Exception as check_err:
                            FreeCAD.Console.PrintWarning(f"    Piece invalid BEFORE cut {i+1}: {check_err}. Skipping this piece.")
                            next_pieces.append(piece) # Keep the invalid piece?
                            continue
                        # -------------------------------------------

                        # Perform the cut
                        try:
                            # Use the box shape as the cutting tool
                            cut_result = piece.cut(tool_shape)
                        except Part.OCCError as cut_err:
                             FreeCAD.Console.PrintWarning(f"    Part.cut operation failed for tool {i+1} on a piece: {cut_err}. Keeping piece.")
                             next_pieces.append(piece) # Keep the piece uncut if cut fails
                             continue
                        except Exception as general_cut_err:
                             FreeCAD.Console.PrintWarning(f"    Unexpected error during Part.cut for tool {i+1}: {general_cut_err}. Keeping piece.")
                             next_pieces.append(piece)
                             continue

                        # Process the result of the cut
                        # (Keep the existing logic for processing cut_result: checking Solids, Volume etc.)
                        if cut_result and not cut_result.isNull() and hasattr(cut_result, 'Solids') and cut_result.Solids:
                             valid_fragments = [s for s in cut_result.Solids if not s.isNull() and s.Volume > 1e-9]
                             if valid_fragments:
                                  next_pieces.extend(valid_fragments)
                             else:
                                  FreeCAD.Console.PrintWarning(f"    Cut resulted in compound but no valid solid fragments for tool {i+1}. Keeping original piece.")
                                  next_pieces.append(piece)
                        elif cut_result and isinstance(cut_result, Part.Solid):
                              next_pieces.append(cut_result)
                        else:
                             FreeCAD.Console.PrintWarning(f"    Cut with tool {i+1} failed or yielded no solids. Keeping original piece.")
                             next_pieces.append(piece)

                    # Update the list of pieces for the next tool cut
                    current_pieces = next_pieces
                    if not current_pieces:
                         FreeCAD.Console.PrintError("  Lost all pieces during cutting process! Aborting.\n")
                         raise ValueError("Splitting process resulted in no pieces.")

                # Final pieces are in current_pieces
                initial_solid_pieces_shapes = [p for p in current_pieces if isinstance(p, Part.Solid) and not p.isNull() and p.Volume > 1e-9]
                FreeCAD.Console.PrintMessage(f"Sequential cutting finished. Found {len(initial_solid_pieces_shapes)} potential solids.\n")

            except Exception as cut_process_err:
                FreeCAD.Console.PrintError(f"Error during Part.cut process: {cut_process_err}\n")
                import traceback
                traceback.print_exc()
                raise ValueError(f"Error during cutting process: {cut_process_err}")

            if not initial_solid_pieces_shapes:
                 raise ValueError("Sequential cutting resulted in zero valid solid pieces.")

            # Create dictionary to hold the CURRENT shape for each piece index
            # We modify these shapes during connector addition
            current_piece_shapes = {i: shape for i, shape in enumerate(initial_solid_pieces_shapes)}

            # --- Connector Logic ---
            if add_connectors and len(initial_solid_pieces_shapes) > 1:
                FreeCAD.Console.PrintMessage("Processing connectors...\n")
                hole_diameter = pin_diameter + 2 * tolerance
                hole_depth = pin_height + max(1.0, tolerance * 2) # Ensure slightly deeper
                processed_interface_pairs = set() # Avoid double processing

                for i in range(len(initial_solid_pieces_shapes)):
                    for j in range(i + 1, len(initial_solid_pieces_shapes)):
                        shape1 = current_piece_shapes[i]
                        shape2 = current_piece_shapes[j]

                        matching_indices = self.find_matching_planar_faces(shape1, shape2, tolerance=0.1) # Increased tolerance for matching

                        if matching_indices:
                            FreeCAD.Console.PrintMessage(f"    Found {len(matching_indices)} potential interface pair(s) between piece {i+1} and piece {j+1}. Checking...")

                            for face1_idx, face2_idx in matching_indices:
                                # --- DEBUG --- 
                                FreeCAD.Console.PrintMessage(f"      Processing interface pair: Piece {i+1} (Face {face1_idx}) <-> Piece {j+1} (Face {face2_idx})")
                                # ------------- 
                                try:
                                    face1 = shape1.Faces[face1_idx]
                                    face2 = shape2.Faces[face2_idx] # Not strictly needed but good for check

                                    center_point = face1.CenterOfMass
                                    normal_vec = face1.normalAt(face1.Surface.parameter(center_point)[0], face1.Surface.parameter(center_point)[1])

                                    # Create Pin (aligned with face1 normal)
                                    pin_placement = Base.Placement(center_point, Base.Rotation(Base.Vector(0,0,1), normal_vec))
                                    pin = Part.makeCylinder(pin_diameter / 2, pin_height, Base.Vector(0,0,0), Base.Vector(0,0,1))
                                    pin.Placement = pin_placement

                                    # Create Hole Cutter (aligned with face2 normal = -face1 normal)
                                    hole_placement = Base.Placement(center_point, Base.Rotation(Base.Vector(0,0,1), -normal_vec))
                                    hole_cutter = Part.makeCylinder(hole_diameter / 2, hole_depth, Base.Vector(0,0,0), Base.Vector(0,0,1))
                                    hole_cutter.Placement = hole_placement

                                    # --- DEBUG --- 
                                    FreeCAD.Console.PrintMessage(f"        Pin Dia: {pin_diameter:.2f}, Hole Dia: {hole_diameter:.2f}, Center: ({center_point.x:.1f},{center_point.y:.1f},{center_point.z:.1f}) ")
                                    # ------------- 

                                    # Apply Booleans (Object 'i' gets pin, Object 'j' gets hole)
                                    FreeCAD.Console.PrintMessage(f"        Applying fuse pin to piece {i+1}...")
                                    new_shape1 = shape1.fuse(pin)
                                    fuse_success = False
                                    if not new_shape1.isNull() and new_shape1.isValid():
                                        # Relaxed volume check (allow small discrepancies)
                                        #if new_shape1.Volume < shape1.Volume - 1e-3:
                                        #    FreeCAD.Console.PrintWarning(f"        Fuse resulted in significant volume decrease for piece {i+1}. Treating as failure.")
                                        #else:
                                        fuse_success = True
                                        FreeCAD.Console.PrintMessage(f"        Fuse successful for piece {i+1}.")
                                    else:
                                        FreeCAD.Console.PrintWarning(f"        Fuse failed or invalid for pin on piece {i+1}. Skipping connector.")

                                    # Proceed only if fuse was successful
                                    if fuse_success:
                                        FreeCAD.Console.PrintMessage(f"        Applying cut hole from piece {j+1}...")
                                        new_shape2 = shape2.cut(hole_cutter)
                                        cut_success = False
                                        if not new_shape2.isNull() and new_shape2.isValid():
                                            # Relaxed volume check
                                            #if new_shape2.Volume > shape2.Volume + 1e-3:
                                            #     FreeCAD.Console.PrintWarning(f"        Cut resulted in significant volume increase for piece {j+1}. Treating as failure.")
                                            #else:
                                            cut_success = True
                                            FreeCAD.Console.PrintMessage(f"        Cut successful for piece {j+1}.")
                                        else:
                                             FreeCAD.Console.PrintWarning(f"        Cut failed or invalid for hole on piece {j+1}. Skipping connector.")

                                        # Update shapes ONLY if BOTH operations succeeded
                                        if cut_success:
                                            current_piece_shapes[i] = new_shape1
                                            current_piece_shapes[j] = new_shape2
                                            processed_interface_pairs.add(interface_key) # Mark as processed
                                            FreeCAD.Console.PrintMessage(f"        Connector added successfully to pair ({i+1}, {j+1}).\n")
                                        else:
                                             FreeCAD.Console.PrintWarning(f"        Cut failed for piece {j+1}, connector NOT added to pair ({i+1}, {j+1}).\n")
                                    else:
                                         FreeCAD.Console.PrintWarning(f"        Fuse failed for piece {i+1}, connector NOT added to pair ({i+1}, {j+1}).\n")

                                except Exception as conn_err:
                                    FreeCAD.Console.PrintWarning(f"    Error applying connector for interface {interface_key}: {conn_err}\n")

            # --- Validation Step ---
            FreeCAD.Console.PrintMessage("Validating final piece sizes...\n")
            invalid_pieces = []
            final_valid_shapes = {} # Store only the shapes that pass validation
            for i, shape in current_piece_shapes.items():
                 try:
                     shape.check() # Check geometry validity first
                     bbox = shape.BoundBox
                     if self.check_fit(bbox, printer_dims):
                         final_valid_shapes[i] = shape
                         FreeCAD.Console.PrintMessage(f"  Piece {i+1} fits (BBox: X={bbox.XLength:.1f}, Y={bbox.YLength:.1f}, Z={bbox.ZLength:.1f}).\n")
                     else:
                         invalid_pieces.append(i + 1)
                         FreeCAD.Console.PrintWarning(f"  ERROR: Piece {i+1} DOES NOT FIT after adding connectors! (BBox: X={bbox.XLength:.1f}, Y={bbox.YLength:.1f}, Z={bbox.ZLength:.1f}).\n")
                 except Exception as val_err:
                      invalid_pieces.append(i + 1)
                      FreeCAD.Console.PrintWarning(f"  ERROR: Piece {i+1} has invalid geometry after connector stage: {val_err}.\n")


            if invalid_pieces:
                 # If any piece failed validation, abort the whole operation
                 failed_list = ", ".join(map(str, invalid_pieces))
                 raise ValueError(f"Operation aborted. The following piece(s) are too large or invalid after adding connectors: {failed_list}. Try smaller connectors or disable them.")

            if not final_valid_shapes:
                 raise ValueError("Operation aborted. No valid pieces remained after validation.")


            # --- Create Final Objects ---
            FreeCAD.Console.PrintMessage("Creating final objects for valid pieces...\n")
            result_group = FreeCAD.ActiveDocument.addObject('App::DocumentObjectGroup', f"{self.obj_to_split.Name}_SplitResult")
            original_obj_gui = FreeCADGui.ActiveDocument.getObject(self.obj_to_split.Name)
            valid_pieces_count = 0

            for i, final_shape in final_valid_shapes.items():
                 piece_name = f"{self.obj_to_split.Name}_split_{i+1}"
                 new_piece_obj = FreeCAD.ActiveDocument.addObject("Part::Feature", piece_name)
                 new_piece_obj.Shape = final_shape
                 piece_objects.append(new_piece_obj) # Add to list for potential future use
                 result_group.addObject(new_piece_obj)
                 valid_pieces_count += 1

                 # Copy visual properties
                 if original_obj_gui and hasattr(original_obj_gui, "ViewObject"):
                    vo_original = original_obj_gui.ViewObject
                    vo_new = new_piece_obj.ViewObject
                    try: # Sometimes accessing properties fails
                        vo_new.ShapeColor = vo_original.ShapeColor
                        vo_new.LineColor = vo_original.LineColor
                        vo_new.Transparency = vo_original.Transparency
                    except: pass


            if valid_pieces_count == 0:
                 # Should be caught by previous check, but just in case
                 raise ValueError("Operation failed: No valid pieces were created.")

            # --- Finalize ---
            FreeCAD.Console.PrintMessage(f"Successfully created {valid_pieces_count} final piece(s).\n")
            if original_obj_gui: original_obj_gui.Visibility = False # Hide original
            FreeCAD.ActiveDocument.commitTransaction() # COMMIT CHANGES
            QtGui.QMessageBox.information(None, "Success", f"Object successfully processed into {valid_pieces_count} pieces.")

        except ValueError as ve: # Catch specific logical/input errors
            FreeCAD.ActiveDocument.abortTransaction()
            FreeCAD.Console.PrintError(f"Processing Error: {ve}\n")
            QtGui.QMessageBox.critical(None, "Error", f"{ve}")
        except Part.OCCError as occ_err: # Catch geometry kernel errors
            FreeCAD.ActiveDocument.abortTransaction()
            FreeCAD.Console.PrintError(f"Geometry Engine Error: {occ_err}\n")
            import traceback
            traceback.print_exc()
            QtGui.QMessageBox.critical(None, "Geometry Error", f"A geometry error occurred:\n{occ_err}\nCheck Report View.")
        except Exception as e: # Catch any other unexpected errors
            FreeCAD.ActiveDocument.abortTransaction()
            FreeCAD.Console.PrintError(f"Unexpected Error: {e}\n")
            import traceback
            traceback.print_exc()
            QtGui.QMessageBox.critical(None, "Error", f"An unexpected error occurred:\n{e}")
        finally:
             # Clean up temporary objects just in case they weren't removed
             if temp_cutter_obj and temp_cutter_obj.Name in FreeCAD.ActiveDocument.Objects:
                 try: FreeCAD.ActiveDocument.removeObject(temp_cutter_obj.Name)
                 except: pass
             # Final recompute and close panel
             try: FreeCAD.ActiveDocument.recompute()
             except: FreeCAD.Console.PrintError("Error during final recompute.\n")
             self.close()


# --- End of PrintSplitterTaskPanel.py --- 