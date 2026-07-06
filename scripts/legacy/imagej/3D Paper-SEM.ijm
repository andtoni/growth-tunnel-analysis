//setTool("rectangle");
makeRectangle(7, 5, 1267, 948);
run("Crop");
run("Enhance Contrast...", "saturated=0.3 equalize");
run("Despeckle");
run("Set Scale...", "distance=250 known=50 pixel=1 unit=microns");
run("Scale Bar...", "width=50 height=20 font=14 color=White background=Black location=[Lower Right] bold hide");
