# state file generated using paraview version 5.13.3
import paraview
paraview.compatibility.major = 5
paraview.compatibility.minor = 13

#### import the simple module from the paraview
from paraview.simple import *
#### disable automatic camera reset on 'Show'
paraview.simple._DisableFirstRenderCameraReset()

# ----------------------------------------------------------------
# setup views used in the visualization
# ----------------------------------------------------------------

# get the material library
materialLibrary1 = GetMaterialLibrary()

# Create a new 'Render View'
renderView1 = CreateView('RenderView')
renderView1.ViewSize = [750, 750]
renderView1.AxesGrid = 'Grid Axes 3D Actor'
renderView1.Size = 145
renderView1.Location = 'Bottom Left'
renderView1.OrientationAxesLabelColor = [0.0, 0.0, 0.0]
renderView1.OrientationAxesOutlineColor = [0.0, 0.0, 0.0]
renderView1.OrientationAxesYColor = [0.0, 0.3333333333333333, 1.0]
renderView1.CenterOfRotation = [161.72999572753906, 162.41521217651368, 162.80289223022461]
renderView1.UseToneMapping = 1
renderView1.Exposure = 1.3
renderView1.StereoType = 'Crystal Eyes'
renderView1.CameraPosition = [789.3732317839928, 790.0584482329673, 790.4461282866783]
renderView1.CameraFocalPoint = [161.72999572753906, 162.41521217651368, 162.80289223022461]
renderView1.CameraViewUp = [-0.4082482904638631, 0.816496580927726, -0.40824829046386296]
renderView1.CameraFocalDisk = 1.0
renderView1.CameraParallelScale = 294.3604668209103
renderView1.CameraParallelProjection = 1
renderView1.LegendGrid = 'Legend Grid Actor'
renderView1.PolarGrid = 'Polar Grid Actor'
renderView1.UseColorPaletteForBackground = 0
renderView1.Background = [1.0, 1.0, 1.0]
renderView1.BackEnd = 'OSPRay raycaster'
renderView1.OSPRayMaterialLibrary = materialLibrary1

# init the 'Grid Axes 3D Actor' selected for 'AxesGrid'
renderView1.AxesGrid.Visibility = 1
renderView1.AxesGrid.XTitle = 'X Axis (um)'
renderView1.AxesGrid.YTitle = 'Y Axis (um)'
renderView1.AxesGrid.ZTitle = 'Z Axis (um)'
renderView1.AxesGrid.XTitleColor = [0.0, 0.0, 0.0]
renderView1.AxesGrid.XTitleFontSize = 20
renderView1.AxesGrid.YTitleColor = [0.0, 0.0, 0.0]
renderView1.AxesGrid.YTitleFontSize = 20
renderView1.AxesGrid.ZTitleColor = [0.0, 0.0, 0.0]
renderView1.AxesGrid.ZTitleFontSize = 22
renderView1.AxesGrid.CullFrontface = 0
renderView1.AxesGrid.GridColor = [0.40784313725490196, 0.40784313725490196, 0.40784313725490196]
renderView1.AxesGrid.XLabelColor = [0.0, 0.0, 0.0]
renderView1.AxesGrid.XLabelFontSize = 22
renderView1.AxesGrid.YLabelColor = [0.0, 0.0, 0.0]
renderView1.AxesGrid.YLabelFontSize = 22
renderView1.AxesGrid.ZLabelColor = [0.0, 0.0, 0.0]
renderView1.AxesGrid.ZLabelFontSize = 22

SetActiveView(None)

# ----------------------------------------------------------------
# setup view layouts
# ----------------------------------------------------------------

# create new layout object 'Layout #1'
layout1 = CreateLayout(name='Layout #1')
layout1.AssignView(0, renderView1)
layout1.SetSize(750, 750)

# ----------------------------------------------------------------
# restore active view
SetActiveView(renderView1)
# ----------------------------------------------------------------

# ----------------------------------------------------------------
# setup the data processing pipelines
# ----------------------------------------------------------------

# create a new 'XML PolyData Reader'
proj_02vtp = XMLPolyDataReader(registrationName='proj_02.vtp', FileName=['C:\\Users\\andto\\OneDrive\\Desktop\\University\\PhD\\DATA\\Transmural Space Characterisation\\3D Analysis Paper\\SR-Pel16\\proj_02.vtp'])
proj_02vtp.CellArrayStatus = ['network | labels | throat | all', 'network | properties | throat | cross_sectional_area', 'network | properties | throat | direct_length', 'network | properties | throat | equivalent_diameter', 'network | properties | throat | inscribed_diameter', 'network | properties | throat | perimeter', 'network | properties | throat | total_length']
proj_02vtp.PointArrayStatus = ['network | labels | pore | all', 'network | labels | pore | boundary', 'network | labels | pore | xmax', 'network | labels | pore | xmin', 'network | labels | pore | ymax', 'network | labels | pore | ymin', 'network | labels | pore | zmax', 'network | labels | pore | zmin', 'network | properties | pore | equivalent_diameter', 'network | properties | pore | extended_diameter', 'network | properties | pore | inscribed_diameter', 'network | properties | pore | phase', 'network | properties | pore | region_label', 'network | properties | pore | region_volume', 'network | properties | pore | surface_area', 'network | properties | pore | volume']
proj_02vtp.TimeArray = 'None'

# create a new 'Cell Data to Point Data'
cellDatatoPointData1 = CellDatatoPointData(registrationName='CellDatatoPointData1', Input=proj_02vtp)
cellDatatoPointData1.CellDataArraytoprocess = ['network | labels | throat | all', 'network | properties | throat | cross_sectional_area', 'network | properties | throat | direct_length', 'network | properties | throat | equivalent_diameter', 'network | properties | throat | inscribed_diameter', 'network | properties | throat | perimeter', 'network | properties | throat | total_length']

# create a new 'TIFF Series Reader'
image2tif = TIFFSeriesReader(registrationName='image2.tif', FileNames=['C:\\Users\\andto\\OneDrive\\Desktop\\University\\PhD\\DATA\\Transmural Space Characterisation\\3D Analysis Paper\\SR-Pel16\\image2.tif'])
image2tif.UseCustomDataSpacing = 1
image2tif.CustomDataSpacing = [0.54, 0.54, 0.54]

# create a new 'TIFF Series Reader'
imagetif = TIFFSeriesReader(registrationName='image.tif', FileNames=['C:\\Users\\andto\\OneDrive\\Desktop\\University\\PhD\\DATA\\Transmural Space Characterisation\\3D Analysis Paper\\SR-Pel16\\image.tif'])
imagetif.UseCustomDataSpacing = 1
imagetif.CustomDataSpacing = [0.54, 0.54, 0.54]

# create a new 'Extract Surface'
extractSurface1 = ExtractSurface(registrationName='ExtractSurface1', Input=cellDatatoPointData1)

# create a new 'Tube'
tube1 = Tube(registrationName='Tube1', Input=extractSurface1)
tube1.Scalars = ['POINTS', 'network | properties | throat | inscribed_diameter']
tube1.Vectors = ['POINTS', '1']
tube1.Radius = 0.520992
tube1.RadiusFactor = 6.0

# create a new 'Clip'
clip1 = Clip(registrationName='Clip1', Input=image2tif)
clip1.ClipType = 'Plane'
clip1.HyperTreeGridClipper = 'Plane'
clip1.Scalars = ['POINTS', 'Tiff Scalars']
clip1.Value = 0.5

# init the 'Plane' selected for 'ClipType'
clip1.ClipType.Origin = [160.964, 161.73, 162.864]
clip1.ClipType.Normal = [-0.779865, 0.214644, 0.587995]

# init the 'Plane' selected for 'HyperTreeGridClipper'
clip1.HyperTreeGridClipper.Origin = [161.73000000000002, 161.73000000000002, 161.73000000000002]

# create a new 'Glyph'
glyph1 = Glyph(registrationName='Glyph1', Input=proj_02vtp,
    GlyphType='Sphere')
glyph1.OrientationArray = ['POINTS', 'No orientation array']
glyph1.ScaleArray = ['POINTS', 'network | properties | pore | inscribed_diameter']
glyph1.ScaleFactor = 0.75
glyph1.GlyphTransform = 'Transform2'

# create a new 'XML PolyData Reader'
growthtunnelvtp = XMLPolyDataReader(registrationName='growthtunnel.vtp', FileName=['C:\\Users\\andto\\OneDrive\\Desktop\\University\\PhD\\DATA\\Transmural Space Characterisation\\3D Analysis Paper\\SR-Pel16\\growthtunnel.vtp'])
growthtunnelvtp.CellArrayStatus = ['network | labels | throat | all', 'network | properties | throat | cross_sectional_area', 'network | properties | throat | diameter', 'network | properties | throat | direct_length', 'network | properties | throat | equivalent_diameter', 'network | properties | throat | inscribed_diameter', 'network | properties | throat | length', 'network | properties | throat | lens_volume', 'network | properties | throat | max_size', 'network | properties | throat | perimeter', 'network | properties | throat | spacing', 'network | properties | throat | total_length', 'network | properties | throat | total_volume', 'network | properties | throat | volume']
growthtunnelvtp.PointArrayStatus = ['network | labels | pore | all', 'network | labels | pore | back', 'network | labels | pore | bottom', 'network | labels | pore | boundary', 'network | labels | pore | front', 'network | labels | pore | left', 'network | labels | pore | right', 'network | labels | pore | top', 'network | labels | pore | xmax', 'network | labels | pore | xmin', 'network | labels | pore | ymax', 'network | labels | pore | ymin', 'network | labels | pore | zmax', 'network | labels | pore | zmin', 'network | properties | pore | coordination_number', 'network | properties | pore | diameter', 'network | properties | pore | equivalent_diameter', 'network | properties | pore | extended_diameter', 'network | properties | pore | inscribed_diameter', 'network | properties | pore | max_size', 'network | properties | pore | phase', 'network | properties | pore | region_label', 'network | properties | pore | region_volume', 'network | properties | pore | seed', 'network | properties | pore | surface_area', 'network | properties | pore | volume']
growthtunnelvtp.TimeArray = 'None'

# create a new 'Glyph'
glyph2 = Glyph(registrationName='Glyph2', Input=growthtunnelvtp,
    GlyphType='Sphere')
glyph2.OrientationArray = ['POINTS', 'No orientation array']
glyph2.ScaleArray = ['POINTS', 'network | properties | pore | inscribed_diameter']
glyph2.ScaleFactor = 0.9
glyph2.GlyphTransform = 'Transform2'

# create a new 'Cell Data to Point Data'
cellDatatoPointData2 = CellDatatoPointData(registrationName='CellDatatoPointData2', Input=growthtunnelvtp)
cellDatatoPointData2.CellDataArraytoprocess = ['network | labels | throat | all', 'network | properties | throat | cross_sectional_area', 'network | properties | throat | diameter', 'network | properties | throat | direct_length', 'network | properties | throat | equivalent_diameter', 'network | properties | throat | inscribed_diameter', 'network | properties | throat | length', 'network | properties | throat | lens_volume', 'network | properties | throat | max_size', 'network | properties | throat | perimeter', 'network | properties | throat | spacing', 'network | properties | throat | total_length', 'network | properties | throat | total_volume', 'network | properties | throat | volume']

# create a new 'Extract Surface'
extractSurface2 = ExtractSurface(registrationName='ExtractSurface2', Input=cellDatatoPointData2)

# create a new 'Tube'
tube2 = Tube(registrationName='Tube2', Input=extractSurface2)
tube2.Scalars = ['POINTS', 'network | properties | throat | inscribed_diameter']
tube2.Vectors = ['POINTS', '1']
tube2.Radius = 2.0
tube2.RadiusFactor = 6.0

# ----------------------------------------------------------------
# setup the visualization in view 'renderView1'
# ----------------------------------------------------------------

# show data from glyph2
glyph2Display = Show(glyph2, renderView1, 'GeometryRepresentation')

# get 2D transfer function for 'networkpropertiesporeinscribed_diameter'
networkpropertiesporeinscribed_diameterTF2D = GetTransferFunction2D('networkpropertiesporeinscribed_diameter')

# get color transfer function/color map for 'networkpropertiesporeinscribed_diameter'
networkpropertiesporeinscribed_diameterLUT = GetColorTransferFunction('networkpropertiesporeinscribed_diameter')
networkpropertiesporeinscribed_diameterLUT.TransferFunction2D = networkpropertiesporeinscribed_diameterTF2D
networkpropertiesporeinscribed_diameterLUT.RGBPoints = [10.015508193969728, 0.0, 1.0, 1.0, 19.228886787414552, 0.0, 0.0, 1.0, 20.252595520019533, 0.0, 0.0, 0.501960784314, 21.276304252624517, 1.0, 0.0, 0.0, 30.489682846069343, 1.0, 1.0, 0.0]
networkpropertiesporeinscribed_diameterLUT.ColorSpace = 'RGB'
networkpropertiesporeinscribed_diameterLUT.ScalarRangeInitialized = 1.0

# trace defaults for the display properties.
glyph2Display.Representation = 'Surface'
glyph2Display.ColorArrayName = ['POINTS', 'network | properties | pore | inscribed_diameter']
glyph2Display.LookupTable = networkpropertiesporeinscribed_diameterLUT
glyph2Display.SelectNormalArray = 'Normals'
glyph2Display.SelectTangentArray = 'None'
glyph2Display.SelectTCoordArray = 'None'
glyph2Display.TextureTransform = 'Transform2'
glyph2Display.OSPRayScaleArray = 'Normals'
glyph2Display.OSPRayScaleFunction = 'Piecewise Function'
glyph2Display.Assembly = ''
glyph2Display.SelectedBlockSelectors = ['']
glyph2Display.SelectOrientationVectors = 'None'
glyph2Display.ScaleFactor = 25.289810943603516
glyph2Display.SelectScaleArray = 'None'
glyph2Display.GlyphType = 'Arrow'
glyph2Display.GlyphTableIndexArray = 'None'
glyph2Display.GaussianRadius = 1.2644905471801757
glyph2Display.SetScaleArray = ['POINTS', 'Normals']
glyph2Display.ScaleTransferFunction = 'Piecewise Function'
glyph2Display.OpacityArray = ['POINTS', 'Normals']
glyph2Display.OpacityTransferFunction = 'Piecewise Function'
glyph2Display.DataAxesGrid = 'Grid Axes Representation'
glyph2Display.PolarAxes = 'Polar Axes Representation'
glyph2Display.SelectInputVectors = ['POINTS', 'Normals']
glyph2Display.WriteLog = ''

# init the 'Piecewise Function' selected for 'ScaleTransferFunction'
glyph2Display.ScaleTransferFunction.Points = [-0.9749279618263245, 0.0, 0.5, 0.0, 0.9749279618263245, 1.0, 0.5, 0.0]

# init the 'Piecewise Function' selected for 'OpacityTransferFunction'
glyph2Display.OpacityTransferFunction.Points = [-0.9749279618263245, 0.0, 0.5, 0.0, 0.9749279618263245, 1.0, 0.5, 0.0]

# init the 'Grid Axes Representation' selected for 'DataAxesGrid'
glyph2Display.DataAxesGrid.XTitle = 'X Axis (um)'
glyph2Display.DataAxesGrid.YTitle = 'Y Axis (um)'
glyph2Display.DataAxesGrid.ZTitle = 'Z Axis (um)'
glyph2Display.DataAxesGrid.XTitleColor = [0.0, 0.0, 0.0]
glyph2Display.DataAxesGrid.XTitleBold = 1
glyph2Display.DataAxesGrid.YTitleColor = [0.0, 0.0, 0.0]
glyph2Display.DataAxesGrid.YTitleBold = 1
glyph2Display.DataAxesGrid.ZTitleColor = [0.0, 0.0, 0.0]
glyph2Display.DataAxesGrid.ZTitleBold = 1
glyph2Display.DataAxesGrid.FacesToRender = 7
glyph2Display.DataAxesGrid.GridColor = [0.0, 0.0, 0.0]
glyph2Display.DataAxesGrid.ShowGrid = 1
glyph2Display.DataAxesGrid.XLabelColor = [0.0, 0.0, 0.0]
glyph2Display.DataAxesGrid.XLabelBold = 1
glyph2Display.DataAxesGrid.YLabelColor = [0.0, 0.0, 0.0]
glyph2Display.DataAxesGrid.YLabelBold = 1
glyph2Display.DataAxesGrid.ZLabelColor = [0.0, 0.0, 0.0]
glyph2Display.DataAxesGrid.ZLabelBold = 1

# show data from tube2
tube2Display = Show(tube2, renderView1, 'GeometryRepresentation')

# get 2D transfer function for 'networkpropertiesthroatinscribed_diameter'
networkpropertiesthroatinscribed_diameterTF2D = GetTransferFunction2D('networkpropertiesthroatinscribed_diameter')

# get color transfer function/color map for 'networkpropertiesthroatinscribed_diameter'
networkpropertiesthroatinscribed_diameterLUT = GetColorTransferFunction('networkpropertiesthroatinscribed_diameter')
networkpropertiesthroatinscribed_diameterLUT.TransferFunction2D = networkpropertiesthroatinscribed_diameterTF2D
networkpropertiesthroatinscribed_diameterLUT.RGBPoints = [10.18869941711426, 1.0, 1.0, 1.0, 20.34480136871338, 0.0, 0.0, 0.0]
networkpropertiesthroatinscribed_diameterLUT.ColorSpace = 'RGB'
networkpropertiesthroatinscribed_diameterLUT.NanColor = [1.0, 0.0, 0.0]
networkpropertiesthroatinscribed_diameterLUT.ScalarRangeInitialized = 1.0

# trace defaults for the display properties.
tube2Display.Representation = 'Surface'
tube2Display.ColorArrayName = ['POINTS', 'network | properties | throat | inscribed_diameter']
tube2Display.LookupTable = networkpropertiesthroatinscribed_diameterLUT
tube2Display.SelectNormalArray = 'TubeNormals'
tube2Display.SelectTangentArray = 'None'
tube2Display.SelectTCoordArray = 'None'
tube2Display.TextureTransform = 'Transform2'
tube2Display.OSPRayScaleArray = 'TubeNormals'
tube2Display.OSPRayScaleFunction = 'Piecewise Function'
tube2Display.Assembly = ''
tube2Display.SelectedBlockSelectors = ['']
tube2Display.SelectOrientationVectors = 'None'
tube2Display.ScaleFactor = 24.475020464175618
tube2Display.SelectScaleArray = 'None'
tube2Display.GlyphType = 'Arrow'
tube2Display.GlyphTableIndexArray = 'None'
tube2Display.GaussianRadius = 1.223751023208781
tube2Display.SetScaleArray = ['POINTS', 'TubeNormals']
tube2Display.ScaleTransferFunction = 'Piecewise Function'
tube2Display.OpacityArray = ['POINTS', 'TubeNormals']
tube2Display.OpacityTransferFunction = 'Piecewise Function'
tube2Display.DataAxesGrid = 'Grid Axes Representation'
tube2Display.PolarAxes = 'Polar Axes Representation'
tube2Display.SelectInputVectors = ['POINTS', 'TubeNormals']
tube2Display.WriteLog = ''

# init the 'Piecewise Function' selected for 'ScaleTransferFunction'
tube2Display.ScaleTransferFunction.Points = [-0.9991629719734192, 0.0, 0.5, 0.0, 0.9991629719734192, 1.0, 0.5, 0.0]

# init the 'Piecewise Function' selected for 'OpacityTransferFunction'
tube2Display.OpacityTransferFunction.Points = [-0.9991629719734192, 0.0, 0.5, 0.0, 0.9991629719734192, 1.0, 0.5, 0.0]

# init the 'Grid Axes Representation' selected for 'DataAxesGrid'
tube2Display.DataAxesGrid.XTitle = 'X Axis (um)'
tube2Display.DataAxesGrid.YTitle = 'Y Axis (um)'
tube2Display.DataAxesGrid.ZTitle = 'Z Axis (um)'
tube2Display.DataAxesGrid.XTitleColor = [0.0, 0.0, 0.0]
tube2Display.DataAxesGrid.XTitleBold = 1
tube2Display.DataAxesGrid.YTitleColor = [0.0, 0.0, 0.0]
tube2Display.DataAxesGrid.YTitleBold = 1
tube2Display.DataAxesGrid.ZTitleColor = [0.0, 0.0, 0.0]
tube2Display.DataAxesGrid.ZTitleBold = 1
tube2Display.DataAxesGrid.FacesToRender = 7
tube2Display.DataAxesGrid.GridColor = [0.0, 0.0, 0.0]
tube2Display.DataAxesGrid.ShowGrid = 1
tube2Display.DataAxesGrid.XLabelColor = [0.0, 0.0, 0.0]
tube2Display.DataAxesGrid.XLabelBold = 1
tube2Display.DataAxesGrid.YLabelColor = [0.0, 0.0, 0.0]
tube2Display.DataAxesGrid.YLabelBold = 1
tube2Display.DataAxesGrid.ZLabelColor = [0.0, 0.0, 0.0]
tube2Display.DataAxesGrid.ZLabelBold = 1

# show data from image2tif
image2tifDisplay = Show(image2tif, renderView1, 'UniformGridRepresentation')

# get 2D transfer function for 'TiffScalars'
tiffScalarsTF2D = GetTransferFunction2D('TiffScalars')
tiffScalarsTF2D.ScalarRangeInitialized = 1

# trace defaults for the display properties.
image2tifDisplay.Representation = 'Surface'
image2tifDisplay.ColorArrayName = ['POINTS', '']
image2tifDisplay.Opacity = 0.0
image2tifDisplay.SelectNormalArray = 'None'
image2tifDisplay.SelectTangentArray = 'None'
image2tifDisplay.SelectTCoordArray = 'None'
image2tifDisplay.TextureTransform = 'Transform2'
image2tifDisplay.OSPRayScaleArray = 'Tiff Scalars'
image2tifDisplay.OSPRayScaleFunction = 'Piecewise Function'
image2tifDisplay.Assembly = ''
image2tifDisplay.SelectedBlockSelectors = ['']
image2tifDisplay.SelectOrientationVectors = 'None'
image2tifDisplay.ScaleFactor = 32.346000000000004
image2tifDisplay.SelectScaleArray = 'Tiff Scalars'
image2tifDisplay.GlyphType = 'Arrow'
image2tifDisplay.GlyphTableIndexArray = 'Tiff Scalars'
image2tifDisplay.GaussianRadius = 1.6173000000000002
image2tifDisplay.SetScaleArray = ['POINTS', 'Tiff Scalars']
image2tifDisplay.ScaleTransferFunction = 'Piecewise Function'
image2tifDisplay.OpacityArray = ['POINTS', 'Tiff Scalars']
image2tifDisplay.OpacityTransferFunction = 'Piecewise Function'
image2tifDisplay.DataAxesGrid = 'Grid Axes Representation'
image2tifDisplay.PolarAxes = 'Polar Axes Representation'
image2tifDisplay.ScalarOpacityUnitDistance = 0.9353074360871939
image2tifDisplay.TransferFunction2D = tiffScalarsTF2D
image2tifDisplay.OpacityArrayName = ['POINTS', 'Tiff Scalars']
image2tifDisplay.ColorArray2Name = ['POINTS', 'Tiff Scalars']
image2tifDisplay.IsosurfaceValues = [0.5]
image2tifDisplay.SliceFunction = 'Plane'
image2tifDisplay.Slice = 299
image2tifDisplay.SelectInputVectors = [None, '']
image2tifDisplay.WriteLog = ''

# init the 'Grid Axes Representation' selected for 'DataAxesGrid'
image2tifDisplay.DataAxesGrid.XTitle = ''
image2tifDisplay.DataAxesGrid.YTitle = ''
image2tifDisplay.DataAxesGrid.ZTitle = ''
image2tifDisplay.DataAxesGrid.XTitleColor = [0.0, 0.0, 0.0]
image2tifDisplay.DataAxesGrid.XTitleBold = 1
image2tifDisplay.DataAxesGrid.XTitleFontSize = 25
image2tifDisplay.DataAxesGrid.YTitleColor = [0.0, 0.0, 0.0]
image2tifDisplay.DataAxesGrid.YTitleBold = 1
image2tifDisplay.DataAxesGrid.YTitleFontSize = 27
image2tifDisplay.DataAxesGrid.ZTitleColor = [0.0, 0.0, 0.0]
image2tifDisplay.DataAxesGrid.ZTitleBold = 1
image2tifDisplay.DataAxesGrid.ZTitleFontSize = 30
image2tifDisplay.DataAxesGrid.FacesToRender = 32
image2tifDisplay.DataAxesGrid.CullFrontface = 0
image2tifDisplay.DataAxesGrid.GridColor = [0.40784313725490196, 0.40784313725490196, 0.40784313725490196]
image2tifDisplay.DataAxesGrid.ShowEdges = 0
image2tifDisplay.DataAxesGrid.LabelUniqueEdgesOnly = 0
image2tifDisplay.DataAxesGrid.AxesToLabel = 39
image2tifDisplay.DataAxesGrid.XLabelColor = [0.0, 0.0, 0.0]
image2tifDisplay.DataAxesGrid.XLabelBold = 1
image2tifDisplay.DataAxesGrid.XLabelFontSize = 25
image2tifDisplay.DataAxesGrid.YLabelColor = [0.0, 0.0, 0.0]
image2tifDisplay.DataAxesGrid.YLabelBold = 1
image2tifDisplay.DataAxesGrid.YLabelFontSize = 25
image2tifDisplay.DataAxesGrid.ZLabelColor = [0.0, 0.0, 0.0]
image2tifDisplay.DataAxesGrid.ZLabelBold = 1
image2tifDisplay.DataAxesGrid.ZLabelFontSize = 25
image2tifDisplay.DataAxesGrid.XAxisUseCustomLabels = 1
image2tifDisplay.DataAxesGrid.XAxisLabels = [0.0, 100.0, 200.0, 300.0]
image2tifDisplay.DataAxesGrid.YAxisUseCustomLabels = 1
image2tifDisplay.DataAxesGrid.YAxisLabels = [0.0, 100.0, 200.0, 300.0]
image2tifDisplay.DataAxesGrid.ZAxisUseCustomLabels = 1
image2tifDisplay.DataAxesGrid.ZAxisLabels = [0.0, 100.0, 200.0, 300.0]

# init the 'Plane' selected for 'SliceFunction'
image2tifDisplay.SliceFunction.Origin = [161.73000000000002, 161.73000000000002, 161.73000000000002]

# setup the color legend parameters for each legend in this view

# get color legend/bar for networkpropertiesthroatinscribed_diameterLUT in view renderView1
networkpropertiesthroatinscribed_diameterLUTColorBar = GetScalarBar(networkpropertiesthroatinscribed_diameterLUT, renderView1)
networkpropertiesthroatinscribed_diameterLUTColorBar.AutoOrient = 0
networkpropertiesthroatinscribed_diameterLUTColorBar.Orientation = 'Horizontal'
networkpropertiesthroatinscribed_diameterLUTColorBar.Position = [0.5857668855838722, 0.009733444629939022]
networkpropertiesthroatinscribed_diameterLUTColorBar.Title = ''
networkpropertiesthroatinscribed_diameterLUTColorBar.ComponentTitle = ''
networkpropertiesthroatinscribed_diameterLUTColorBar.TitleColor = [0.0, 0.0, 0.0]
networkpropertiesthroatinscribed_diameterLUTColorBar.TitleBold = 1
networkpropertiesthroatinscribed_diameterLUTColorBar.TitleFontSize = 30
networkpropertiesthroatinscribed_diameterLUTColorBar.LabelColor = [0.0, 0.0, 0.0]
networkpropertiesthroatinscribed_diameterLUTColorBar.LabelBold = 1
networkpropertiesthroatinscribed_diameterLUTColorBar.LabelFontSize = 30
networkpropertiesthroatinscribed_diameterLUTColorBar.ScalarBarThickness = 25
networkpropertiesthroatinscribed_diameterLUTColorBar.ScalarBarLength = 0.3999999999999999
networkpropertiesthroatinscribed_diameterLUTColorBar.AddRangeLabels = 0

# set color bar visibility
networkpropertiesthroatinscribed_diameterLUTColorBar.Visibility = 1

# get color legend/bar for networkpropertiesporeinscribed_diameterLUT in view renderView1
networkpropertiesporeinscribed_diameterLUTColorBar = GetScalarBar(networkpropertiesporeinscribed_diameterLUT, renderView1)
networkpropertiesporeinscribed_diameterLUTColorBar.AutoOrient = 0
networkpropertiesporeinscribed_diameterLUTColorBar.Orientation = 'Horizontal'
networkpropertiesporeinscribed_diameterLUTColorBar.WindowLocation = 'Upper Left Corner'
networkpropertiesporeinscribed_diameterLUTColorBar.Position = [0.009333333333333332, 0.8779647965262986]
networkpropertiesporeinscribed_diameterLUTColorBar.Title = ''
networkpropertiesporeinscribed_diameterLUTColorBar.ComponentTitle = ''
networkpropertiesporeinscribed_diameterLUTColorBar.TitleColor = [0.0, 0.0, 0.0]
networkpropertiesporeinscribed_diameterLUTColorBar.TitleBold = 1
networkpropertiesporeinscribed_diameterLUTColorBar.TitleFontSize = 30
networkpropertiesporeinscribed_diameterLUTColorBar.LabelColor = [0.0, 0.0, 0.0]
networkpropertiesporeinscribed_diameterLUTColorBar.LabelBold = 1
networkpropertiesporeinscribed_diameterLUTColorBar.LabelFontSize = 30
networkpropertiesporeinscribed_diameterLUTColorBar.ScalarBarThickness = 25
networkpropertiesporeinscribed_diameterLUTColorBar.ScalarBarLength = 0.40000000000000024
networkpropertiesporeinscribed_diameterLUTColorBar.AddRangeLabels = 0
networkpropertiesporeinscribed_diameterLUTColorBar.RangeLabelFormat = '0'
networkpropertiesporeinscribed_diameterLUTColorBar.DataRangeLabelFormat = ''
networkpropertiesporeinscribed_diameterLUTColorBar.TextPosition = 'Ticks left/bottom, annotations right/top'

# set color bar visibility
networkpropertiesporeinscribed_diameterLUTColorBar.Visibility = 1

# show color legend
glyph2Display.SetScalarBarVisibility(renderView1, True)

# show color legend
tube2Display.SetScalarBarVisibility(renderView1, True)

# ----------------------------------------------------------------
# setup color maps and opacity maps used in the visualization
# note: the Get..() functions create a new object, if needed
# ----------------------------------------------------------------

# get opacity transfer function/opacity map for 'networkpropertiesthroatinscribed_diameter'
networkpropertiesthroatinscribed_diameterPWF = GetOpacityTransferFunction('networkpropertiesthroatinscribed_diameter')
networkpropertiesthroatinscribed_diameterPWF.Points = [10.18869941711426, 0.0, 0.5, 0.0, 20.34480136871338, 1.0, 0.5, 0.0]
networkpropertiesthroatinscribed_diameterPWF.ScalarRangeInitialized = 1

# get opacity transfer function/opacity map for 'networkpropertiesporeinscribed_diameter'
networkpropertiesporeinscribed_diameterPWF = GetOpacityTransferFunction('networkpropertiesporeinscribed_diameter')
networkpropertiesporeinscribed_diameterPWF.Points = [10.015508193969728, 0.0, 0.5, 0.0, 30.489682846069343, 1.0, 0.5, 0.0]
networkpropertiesporeinscribed_diameterPWF.ScalarRangeInitialized = 1

# ----------------------------------------------------------------
# setup animation scene, tracks and keyframes
# note: the Get..() functions create a new object, if needed
# ----------------------------------------------------------------

# get time animation track
timeAnimationCue1 = GetTimeTrack()

# initialize the animation scene

# get the time-keeper
timeKeeper1 = GetTimeKeeper()

# initialize the timekeeper

# initialize the animation track

# get animation scene
animationScene1 = GetAnimationScene()

# initialize the animation scene
animationScene1.ViewModules = renderView1
animationScene1.Cues = timeAnimationCue1
animationScene1.AnimationTime = 0.0

# ----------------------------------------------------------------
# restore active source
SetActiveSource(image2tif)
# ----------------------------------------------------------------


##--------------------------------------------
## You may need to add some code at the end of this python script depending on your usage, eg:
#
## Render all views to see them appears
# RenderAllViews()
#
## Interact with the view, usefull when running from pvpython
# Interact()
#
## Save a screenshot of the active view
# SaveScreenshot("path/to/screenshot.png")
#
## Save a screenshot of a layout (multiple splitted view)
# SaveScreenshot("path/to/screenshot.png", GetLayout())
#
## Save all "Extractors" from the pipeline browser
# SaveExtracts()
#
## Save a animation of the current active view
# SaveAnimation()
#
## Please refer to the documentation of paraview.simple
## https://www.paraview.org/paraview-docs/latest/python/paraview.simple.html
##--------------------------------------------