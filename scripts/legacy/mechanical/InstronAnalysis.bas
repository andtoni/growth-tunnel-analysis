' =============================================================================
' INSTRON 5544 MECHANICAL DATA ANALYSIS MACRO  (v3 - defensive build)
' Electrospun Pellethane Scaffold Tensile Testing
' =============================================================================
'
' HOW TO USE
'   1. Open a NEW blank Excel workbook (save as .xlsm)
'   2. Press Alt+F11  (VBA editor)
'   3. File > Import File > select this .bas
'   4. Close VBA editor (Alt+F11)
'   5. Press Alt+F8 > select "AnalyzeMechanicalData" > Run
' =============================================================================

Option Explicit

' --- CONFIG ---
Const DATA_FOLDER       As String  = "C:\Users\andto\OneDrive\Desktop\University\Papers\PhD\Paper 2\Extra Analysis\Mechanical\"
Const DOGBONE_WIDTH_MM  As Double  = 4.01
Const GAUGE_LENGTH_MM   As Double  = 21.82
Const THICKNESS_P16     As Double  = 0.3575
Const THICKNESS_P18     As Double  = 0.423
Const THICKNESS_P20     As Double  = 0.4215
Const SECANT_STRAIN_PCT As Double  = 20#
Const TANGENT_WINDOW    As Integer = 7
Const COL_ROW_ALT       As Long    = 15395562

' --- TYPE  (member names chosen to NEVER collide with Excel built-ins) ---
Type TSpec
    sFile        As String
    sName        As String
    sGroupID     As String
    sPEL         As String
    sFR          As String
    sOrient      As String        ' "C" or "L"
    iRep         As Integer
    dThick       As Double
    dArea        As Double
    sDataSheet   As String
    dUTS         As Double
    dEpsBreak    As Double
    dLoadUTS     As Double
    dEsec        As Double
    dEt          As Double
    dKappa       As Double
    bValid       As Boolean
End Type

' ============================================================
' MAIN
' ============================================================
Sub AnalyzeMechanicalData()

    Dim wb           As Workbook
    Dim wsItem       As Worksheet
    Dim wsSummary    As Worksheet
    Dim fso          As Object
    Dim fItem        As Object
    Dim res(500)     As TSpec
    Dim nRes         As Integer
    Dim delNames(500) As String
    Dim nDel         As Integer
    Dim iDel         As Integer
    Dim fPath        As String

    Application.ScreenUpdating = False
    Application.Calculation    = xlCalculationManual
    Application.StatusBar      = "Starting..."

    Set wb = ThisWorkbook

    ' Remove stale specimen sheets
    nDel = 0
    For Each wsItem In wb.Worksheets
        If wsItem.Name <> "Summary" Then
            delNames(nDel) = wsItem.Name
            nDel = nDel + 1
        End If
    Next wsItem
    Application.DisplayAlerts = False
    For iDel = 0 To nDel - 1
        On Error Resume Next
        wb.Worksheets(delNames(iDel)).Delete
        On Error GoTo 0
    Next iDel
    Application.DisplayAlerts = True

    ' Create/clear Summary
    Set wsSummary = Nothing
    On Error Resume Next
    Set wsSummary = wb.Worksheets("Summary")
    On Error GoTo 0
    If wsSummary Is Nothing Then
        Set wsSummary = wb.Worksheets.Add(Before:=wb.Worksheets(1))
        wsSummary.Name = "Summary"
    Else
        wsSummary.Cells.Clear
    End If

    ' Folder check (add trailing backslash if missing)
    fPath = DATA_FOLDER
    If Right(fPath, 1) <> "\" Then fPath = fPath & "\"

    Set fso = CreateObject("Scripting.FileSystemObject")
    If Not fso.FolderExists(fPath) Then
        MsgBox "Folder not found:" & vbNewLine & fPath, vbCritical
        GoTo Done
    End If

    ' Loop .raw files
    nRes = 0
    For Each fItem In fso.GetFolder(fPath).Files
        If LCase(Right(fItem.Name, 4)) = ".raw" Then
            Application.StatusBar = "Processing: " & fItem.Name
            If ProcessFile(wb, fItem.Path, fItem.Name, res(nRes)) Then
                nRes = nRes + 1
            End If
        End If
    Next fItem

    If nRes = 0 Then
        MsgBox "No .raw files in:" & vbNewLine & fPath, vbExclamation
        GoTo Done
    End If

    SortRes res, nRes
    Application.StatusBar = "Writing Summary..."
    WriteSummary wsSummary, res, nRes

    wsSummary.Activate
    wsSummary.Cells(1, 1).Select
    MsgBox nRes & " specimen(s) processed.", vbInformation, "Done"

Done:
    Application.ScreenUpdating = True
    Application.Calculation    = xlCalculationAutomatic
    Application.StatusBar      = False
End Sub

' ============================================================
' PROCESS A SINGLE .RAW FILE
' ============================================================
Function ProcessFile(wb As Workbook, fpath As String, _
                     fname As String, ByRef rs As TSpec) As Boolean
    Dim fNum     As Integer
    Dim lineTxt  As String
    Dim hdrFound As Boolean
    Dim cTime    As Integer
    Dim cExt     As Integer
    Dim cLoad    As Integer
    Dim cStrain  As Integer
    Dim hdr()    As String
    Dim ih       As Integer
    Dim hv       As String
    Dim maxR     As Long
    Dim arT()    As Double
    Dim arE()    As Double
    Dim arL()    As Double
    Dim arS()    As Double
    Dim arSig()  As Double
    Dim nr       As Long
    Dim flds()   As String
    Dim j        As Long
    Dim shName   As String
    Dim wsSpec   As Worksheet
    Dim peakIdx  As Long

    ProcessFile = False
    ParseName fname, rs

    fNum = FreeFile()
    On Error GoTo FileErr
    Open fpath For Input As #fNum

    hdrFound = False
    cTime = 0: cExt = 0: cLoad = 0: cStrain = 0

    Do While Not EOF(fNum)
        Line Input #fNum, lineTxt
        If InStr(lineTxt, "Time sec") > 0 Then
            hdr = SplitCSV(lineTxt)
            For ih = 0 To UBound(hdr)
                hv = LCase(Trim(hdr(ih)))
                If InStr(hv, "time") > 0 And cTime = 0   Then cTime = ih + 1
                If hv = "extension mm"                    Then cExt = ih + 1
                If hv = "load n"                          Then cLoad = ih + 1
                If InStr(hv, "tensile strain") > 0        Then cStrain = ih + 1
            Next ih
            If cTime = 0   Then cTime = 1
            If cExt = 0    Then cExt = 2
            If cLoad = 0   Then cLoad = 3
            If cStrain = 0 Then cStrain = 9
            hdrFound = True
            Exit Do
        End If
    Loop

    If Not hdrFound Then
        Close #fNum
        MsgBox "No data header in " & fname, vbExclamation
        Exit Function
    End If

    maxR = 60000
    ReDim arT(maxR)
    ReDim arE(maxR)
    ReDim arL(maxR)
    ReDim arS(maxR)
    nr = 0

    Do While Not EOF(fNum) And nr < maxR
        Line Input #fNum, lineTxt
        lineTxt = Trim(lineTxt)
        If Len(lineTxt) = 0 Then GoTo SkipLine
        flds = SplitCSV(lineTxt)
        If UBound(flds) < 2 Then GoTo SkipLine
        On Error Resume Next
        arT(nr) = CDbl(GetField(flds, cTime - 1))
        arE(nr) = CDbl(GetField(flds, cExt - 1))
        arL(nr) = CDbl(GetField(flds, cLoad - 1))
        If cStrain - 1 <= UBound(flds) Then
            arS(nr) = CDbl(GetField(flds, cStrain - 1))
        ElseIf GAUGE_LENGTH_MM > 0 Then
            arS(nr) = (arE(nr) / GAUGE_LENGTH_MM) * 100
        End If
        If Err.Number = 0 Then nr = nr + 1
        Err.Clear
        On Error GoTo FileErr
SkipLine:
    Loop
    Close #fNum

    If nr < 5 Then
        MsgBox "Too few rows in " & fname, vbExclamation
        Exit Function
    End If

    ReDim Preserve arT(nr - 1)
    ReDim Preserve arE(nr - 1)
    ReDim Preserve arL(nr - 1)
    ReDim Preserve arS(nr - 1)
    ReDim arSig(nr - 1)

    For j = 0 To nr - 1
        If rs.dArea > 0 Then arSig(j) = arL(j) / rs.dArea
    Next j

    shName = Left(rs.sName, 31)
    Set wsSpec = wb.Worksheets.Add(After:=wb.Worksheets(wb.Worksheets.Count))
    wsSpec.Name = shName
    rs.sDataSheet = shName

    WriteSpecSheet wsSpec, rs, arT, arE, arL, arS, arSig, nr

    peakIdx       = FindPeak(arSig, nr)
    rs.dUTS       = arSig(peakIdx)
    rs.dEpsBreak  = arS(peakIdx)
    rs.dLoadUTS   = arL(peakIdx)
    rs.dEsec      = CalcSecant(arS, arSig, nr, SECANT_STRAIN_PCT)
    rs.dEt        = CalcTangent(arS, arSig, nr, TANGENT_WINDOW)
    rs.dKappa     = CalcTough(arS, arSig, peakIdx)
    rs.bValid     = True

    WriteSpecProps wsSpec, rs, nr

    ProcessFile = True
    Exit Function

FileErr:
    On Error GoTo 0
    If fNum > 0 Then Close #fNum
    MsgBox "Error reading " & fname & ":" & vbNewLine & Err.Description, vbCritical
    ProcessFile = False
End Function

' ============================================================
' WRITE SPECIMEN SHEET (raw data + meta)
' ============================================================
Sub WriteSpecSheet(ws As Worksheet, rs As TSpec, _
                   arT() As Double, arE() As Double, _
                   arL() As Double, arS() As Double, _
                   arSig() As Double, nr As Long)
    Dim j  As Long
    Dim r  As Long
    Dim dh As Integer
    Dim c  As Integer

    ws.Range("A1:F1").Merge
    ws.Cells(1, 1).Value = "Specimen: " & rs.sName
    StyleTitle ws.Cells(1, 1)

    ws.Cells(2, 1).Value = "Group":        ws.Cells(2, 2).Value = rs.sGroupID
    ws.Cells(3, 1).Value = "Direction":    ws.Cells(3, 2).Value = OrientLabel(rs.sOrient)
    ws.Cells(4, 1).Value = "Repeat":       ws.Cells(4, 2).Value = rs.iRep
    ws.Cells(2, 3).Value = "PEL wt%":      ws.Cells(2, 4).Value = rs.sPEL & " %"
    ws.Cells(3, 3).Value = "Flow Rate":    ws.Cells(3, 4).Value = rs.sFR & " ml/hr"
    ws.Cells(4, 3).Value = "Thickness":    ws.Cells(4, 4).Value = rs.dThick & " mm"
    ws.Cells(2, 5).Value = "Width":         ws.Cells(2, 6).Value = DOGBONE_WIDTH_MM & " mm"
    ws.Cells(3, 5).Value = "Gauge Length":  ws.Cells(3, 6).Value = GAUGE_LENGTH_MM & " mm"
    ws.Cells(4, 5).Value = "X-Sect Area":   ws.Cells(4, 6).Value = Format(rs.dArea, "0.0000") & " mm2"

    For c = 1 To 5 Step 2
        ws.Range(ws.Cells(2, c), ws.Cells(4, c)).Font.Bold = True
    Next c

    dh = 6
    ws.Cells(dh, 1).Value = "Time (s)"
    ws.Cells(dh, 2).Value = "Extension (mm)"
    ws.Cells(dh, 3).Value = "Load (N)"
    ws.Cells(dh, 4).Value = "Tensile Strain (%)"
    ws.Cells(dh, 5).Value = "Stress (MPa)"
    StyleColHdr ws.Range(ws.Cells(dh, 1), ws.Cells(dh, 5))

    For j = 0 To nr - 1
        r = dh + 1 + j
        ws.Cells(r, 1).Value = arT(j)
        ws.Cells(r, 2).Value = arE(j)
        ws.Cells(r, 3).Value = arL(j)
        ws.Cells(r, 4).Value = arS(j)
        ws.Cells(r, 5).Value = arSig(j)
        If j Mod 2 = 0 Then
            ws.Range(ws.Cells(r, 1), ws.Cells(r, 5)).Interior.Color = COL_ROW_ALT
        End If
    Next j

    ws.Range(ws.Cells(dh + 1, 1), ws.Cells(dh + nr, 5)).NumberFormat = "0.00000"
    ws.Columns("A:E").AutoFit
    ws.Columns("A").ColumnWidth = 12
    ws.Cells.Font.Name = "Arial"
End Sub

' ============================================================
' WRITE PROPERTIES BLOCK ON SPECIMEN SHEET
' ============================================================
Sub WriteSpecProps(ws As Worksheet, rs As TSpec, nr As Long)
    Dim startRow As Long
    Dim p        As Variant
    Dim i        As Integer
    Dim rr       As Long

    startRow = 8 + nr + 2
    ws.Range(ws.Cells(startRow, 1), ws.Cells(startRow, 3)).Merge
    ws.Cells(startRow, 1).Value = "COMPUTED MECHANICAL PROPERTIES"
    StyleSection ws.Cells(startRow, 1)
    startRow = startRow + 1

    p = Array( _
        "UTS",                              rs.dUTS,       "MPa", _
        "Elongation at Break",              rs.dEpsBreak,  "%", _
        "Load at UTS",                      rs.dLoadUTS,   "N", _
        "Cross-Sectional Area",             rs.dArea,      "mm2", _
        "20% Secant Modulus (E_sec)",       rs.dEsec,      "MPa", _
        "Tangent Modulus at Break (E_t)",   rs.dEt,        "MPa", _
        "Toughness (kappa)",                rs.dKappa,     "MJ/m3" _
    )

    For i = 0 To UBound(p) - 2 Step 3
        rr = startRow + (i \ 3)
        ws.Cells(rr, 1).Value = p(i)
        ws.Cells(rr, 2).Value = p(i + 1)
        ws.Cells(rr, 3).Value = p(i + 2)
        ws.Cells(rr, 1).Font.Bold = True
        ws.Cells(rr, 2).NumberFormat = "0.00000"
        If (i \ 3) Mod 2 = 0 Then
            ws.Range(ws.Cells(rr, 1), ws.Cells(rr, 3)).Interior.Color = COL_ROW_ALT
        End If
    Next i
    ws.Columns("A:C").AutoFit
End Sub

' ============================================================
' WRITE THE SUMMARY SHEET
' ============================================================
Sub WriteSummary(ws As Worksheet, res() As TSpec, n As Integer)
    Dim sr          As Long
    Dim i           As Integer
    Dim g           As Integer
    Dim ug          As Integer
    Dim ic          As Integer
    Dim sc          As Integer
    Dim ac          As Integer
    Dim ni          As Integer
    Dim gc          As Integer
    Dim ugc         As Integer
    Dim vc          As Integer
    Dim prevGD      As String
    Dim curGD       As String
    Dim gdKey       As String
    Dim wasFound    As Boolean
    Dim ugWasFound  As Boolean
    Dim grpArr(200) As String
    Dim dirArr(200) As String
    Dim ugArr(100)  As String
    Dim uArr(200)   As Double
    Dim eArr(200)   As Double
    Dim esArr(200)  As Double
    Dim etArr(200)  As Double
    Dim tkArr(200)  As Double
    Dim mu  As Double, sdU  As Double
    Dim mElon  As Double, sdElon  As Double
    Dim mEs As Double, sdEs As Double
    Dim mEt As Double, sdEt As Double
    Dim mT  As Double, sdT  As Double
    Dim cU  As Double, lU   As Double
    Dim cE  As Double, lE   As Double
    Dim cEs As Double, lEs  As Double
    Dim circEt As Double, longEt  As Double
    Dim cT  As Double, lT   As Double
    Dim nC  As Integer, nL  As Integer
    Dim hdrs1() As Variant
    Dim hdrs2() As Variant
    Dim hdrs3() As Variant
    Dim notes() As Variant

    ws.Cells.Clear
    ws.Cells.Font.Name = "Arial"

    ws.Range("A1:N1").Merge
    ws.Cells(1, 1).Value = "Electrospun Pellethane Scaffold - Tensile Mechanical Properties Summary"
    StyleTitle ws.Cells(1, 1)
    ws.Cells(2, 1).Value = "Dogbone: Width = " & DOGBONE_WIDTH_MM & " mm  |  Gauge Length = " & GAUGE_LENGTH_MM & " mm"
    ws.Cells(3, 1).Value = "Thickness: p16 = " & THICKNESS_P16 & " mm  |  p18 = " & THICKNESS_P18 & " mm  |  p20 = " & THICKNESS_P20 & " mm"
    ws.Cells(4, 1).Value = "Stress = Load(N) / (width x group thickness).  E_sec at 20% strain.  E_t = local OLS slope at fracture point."
    ws.Range("A2:N4").Font.Italic = True
    ws.Range("A2:N4").Font.Size = 9

    ' --- SECTION 1 ---
    sr = 6
    ws.Range(ws.Cells(sr, 1), ws.Cells(sr, 14)).Merge
    ws.Cells(sr, 1).Value = "SECTION 1 - INDIVIDUAL SPECIMEN RESULTS"
    StyleSection ws.Cells(sr, 1)
    sr = sr + 1

    hdrs1 = Array("File Name", "Group", "PEL wt%", "Flow Rate (ml/hr)", _
                  "Direction", "Repeat", "Thickness (mm)", "X-Section (mm2)", _
                  "UTS (MPa)", "Elong. at Break (%)", "Load at UTS (N)", _
                  "E_sec 20% (MPa)", "E_t at Break (MPa)", "Toughness (MJ/m3)")
    For ic = 0 To UBound(hdrs1)
        ws.Cells(sr, ic + 1).Value = hdrs1(ic)
    Next ic
    StyleColHdr ws.Range(ws.Cells(sr, 1), ws.Cells(sr, 14))
    ws.Rows(sr).RowHeight = 42
    sr = sr + 1

    prevGD = ""
    For i = 0 To n - 1
        If Not res(i).bValid Then GoTo SkipSpec
        curGD = res(i).sGroupID & res(i).sOrient
        If curGD <> prevGD And prevGD <> "" Then sr = sr + 1
        prevGD = curGD

        ws.Cells(sr, 1).Value = res(i).sFile
        ws.Cells(sr, 2).Value = res(i).sGroupID
        ws.Cells(sr, 3).Value = res(i).sPEL
        ws.Cells(sr, 4).Value = res(i).sFR
        ws.Cells(sr, 5).Value = OrientLabel(res(i).sOrient)
        ws.Cells(sr, 6).Value = res(i).iRep
        ws.Cells(sr, 7).Value = res(i).dThick
        ws.Cells(sr, 8).Value = res(i).dArea
        ws.Cells(sr, 9).Value = res(i).dUTS
        ws.Cells(sr, 10).Value = res(i).dEpsBreak
        ws.Cells(sr, 11).Value = res(i).dLoadUTS
        ws.Cells(sr, 12).Value = res(i).dEsec
        ws.Cells(sr, 13).Value = res(i).dEt
        ws.Cells(sr, 14).Value = res(i).dKappa

        If res(i).sDataSheet <> "" Then
            ws.Hyperlinks.Add Anchor:=ws.Cells(sr, 1), Address:="", _
                SubAddress:="'" & res(i).sDataSheet & "'!A1", _
                TextToDisplay:=res(i).sFile
        End If

        ws.Range(ws.Cells(sr, 7), ws.Cells(sr, 14)).NumberFormat = "0.0000"
        ws.Cells(sr, 10).NumberFormat = "0.00"
        If sr Mod 2 = 0 Then
            ws.Range(ws.Cells(sr, 1), ws.Cells(sr, 14)).Interior.Color = COL_ROW_ALT
        End If
        sr = sr + 1
SkipSpec:
    Next i

    ' --- SECTION 2: Group stats ---
    sr = sr + 2
    ws.Range(ws.Cells(sr, 1), ws.Cells(sr, 13)).Merge
    ws.Cells(sr, 1).Value = "SECTION 2 - GROUP STATISTICS (Mean and SD)"
    StyleSection ws.Cells(sr, 1)
    sr = sr + 1

    hdrs2 = Array("Group", "Direction", "n", _
                  "UTS (MPa)", "SD", _
                  "Elong. (%)", "SD", _
                  "E_sec (MPa)", "SD", _
                  "E_t (MPa)", "SD", _
                  "Toughness (MJ/m3)", "SD")
    For sc = 0 To UBound(hdrs2)
        ws.Cells(sr, sc + 1).Value = hdrs2(sc)
    Next sc
    StyleColHdr ws.Range(ws.Cells(sr, 1), ws.Cells(sr, 13))
    ws.Rows(sr).RowHeight = 42
    sr = sr + 1

    gc = 0
    For i = 0 To n - 1
        If Not res(i).bValid Then GoTo SkipGC
        gdKey = res(i).sGroupID & "|" & res(i).sOrient
        wasFound = False
        For g = 0 To gc - 1
            If grpArr(g) & "|" & dirArr(g) = gdKey Then
                wasFound = True
                Exit For
            End If
        Next g
        If Not wasFound Then
            grpArr(gc) = res(i).sGroupID
            dirArr(gc) = res(i).sOrient
            gc = gc + 1
        End If
SkipGC:
    Next i

    For g = 0 To gc - 1
        vc = 0
        For i = 0 To n - 1
            If res(i).bValid Then
                If res(i).sGroupID = grpArr(g) And res(i).sOrient = dirArr(g) Then
                    uArr(vc) = res(i).dUTS
                    eArr(vc) = res(i).dEpsBreak
                    esArr(vc) = res(i).dEsec
                    etArr(vc) = res(i).dEt
                    tkArr(vc) = res(i).dKappa
                    vc = vc + 1
                End If
            End If
        Next i
        If vc = 0 Then GoTo SkipGStats

        CalcMeanSD uArr,  vc, mu,  sdU
        CalcMeanSD eArr,  vc, mElon,  sdElon
        CalcMeanSD esArr, vc, mEs, sdEs
        CalcMeanSD etArr, vc, mEt, sdEt
        CalcMeanSD tkArr, vc, mT,  sdT

        ws.Cells(sr, 1).Value = grpArr(g)
        ws.Cells(sr, 2).Value = OrientLabel(dirArr(g))
        ws.Cells(sr, 3).Value = vc
        ws.Cells(sr, 4).Value = mu
        ws.Cells(sr, 5).Value = sdU
        ws.Cells(sr, 6).Value = mElon
        ws.Cells(sr, 7).Value = sdElon
        ws.Cells(sr, 8).Value = mEs
        ws.Cells(sr, 9).Value = sdEs
        ws.Cells(sr, 10).Value = mEt
        ws.Cells(sr, 11).Value = sdEt
        ws.Cells(sr, 12).Value = mT
        ws.Cells(sr, 13).Value = sdT
        ws.Range(ws.Cells(sr, 4), ws.Cells(sr, 13)).NumberFormat = "0.0000"
        ws.Cells(sr, 6).NumberFormat = "0.00"
        ws.Cells(sr, 7).NumberFormat = "0.00"
        If sr Mod 2 = 0 Then
            ws.Range(ws.Cells(sr, 1), ws.Cells(sr, 13)).Interior.Color = COL_ROW_ALT
        End If
        sr = sr + 1
SkipGStats:
    Next g

    ' --- SECTION 3: Anisotropy ---
    sr = sr + 2
    ws.Range(ws.Cells(sr, 1), ws.Cells(sr, 8)).Merge
    ws.Cells(sr, 1).Value = "SECTION 3 - MECHANICAL ANISOTROPY (Circumferential / Longitudinal)"
    StyleSection ws.Cells(sr, 1)
    sr = sr + 1

    hdrs3 = Array("Group", "n (C)", "n (L)", _
                  "AR UTS", "AR Elong.", "AR E_sec", "AR E_t", "AR Toughness")
    For ac = 0 To UBound(hdrs3)
        ws.Cells(sr, ac + 1).Value = hdrs3(ac)
    Next ac
    StyleColHdr ws.Range(ws.Cells(sr, 1), ws.Cells(sr, 8))
    ws.Rows(sr).RowHeight = 42
    sr = sr + 1

    ugc = 0
    For g = 0 To gc - 1
        ugWasFound = False
        For ug = 0 To ugc - 1
            If ugArr(ug) = grpArr(g) Then
                ugWasFound = True
                Exit For
            End If
        Next ug
        If Not ugWasFound Then
            ugArr(ugc) = grpArr(g)
            ugc = ugc + 1
        End If
    Next g

    For ug = 0 To ugc - 1
        cU = 0: lU = 0: cE = 0: lE = 0
        cEs = 0: lEs = 0: circEt = 0: longEt = 0
        cT = 0: lT = 0
        nC = 0: nL = 0
        For i = 0 To n - 1
            If res(i).bValid Then
                If res(i).sGroupID = ugArr(ug) Then
                    If res(i).sOrient = "C" Then
                        cU = cU + res(i).dUTS
                        cE = cE + res(i).dEpsBreak
                        cEs = cEs + res(i).dEsec
                        circEt = circEt + res(i).dEt
                        cT = cT + res(i).dKappa
                        nC = nC + 1
                    ElseIf res(i).sOrient = "L" Then
                        lU = lU + res(i).dUTS
                        lE = lE + res(i).dEpsBreak
                        lEs = lEs + res(i).dEsec
                        longEt = longEt + res(i).dEt
                        lT = lT + res(i).dKappa
                        nL = nL + 1
                    End If
                End If
            End If
        Next i

        ws.Cells(sr, 1).Value = ugArr(ug)
        ws.Cells(sr, 2).Value = nC
        ws.Cells(sr, 3).Value = nL

        If nC > 0 And nL > 0 Then
            If lU > 0 Then  ws.Cells(sr, 4).Value = (cU / nC)  / (lU / nL)
            If lE > 0 Then  ws.Cells(sr, 5).Value = (cE / nC)  / (lE / nL)
            If lEs > 0 Then ws.Cells(sr, 6).Value = (cEs / nC) / (lEs / nL)
            If longEt > 0 Then ws.Cells(sr, 7).Value = (circEt / nC) / (longEt / nL)
            If lT > 0 Then  ws.Cells(sr, 8).Value = (cT / nC)  / (lT / nL)
            ws.Range(ws.Cells(sr, 4), ws.Cells(sr, 8)).NumberFormat = "0.000"
        Else
            ws.Range(ws.Cells(sr, 4), ws.Cells(sr, 8)).Value = "N/A"
        End If

        If sr Mod 2 = 0 Then
            ws.Range(ws.Cells(sr, 1), ws.Cells(sr, 8)).Interior.Color = COL_ROW_ALT
        End If
        sr = sr + 1
    Next ug

    ' --- SECTION 4: Notes ---
    sr = sr + 2
    ws.Range(ws.Cells(sr, 1), ws.Cells(sr, 8)).Merge
    ws.Cells(sr, 1).Value = "SECTION 4 - METRICS AND NOTES FOR PUBLICATION"
    StyleSection ws.Cells(sr, 1)
    sr = sr + 1

    notes = Array( _
        "UTS (MPa)", _
            "Peak engineering stress. Recalculated as Load(N) / (4.01 mm width x group mean thickness).", _
        "Elongation at Break (%)", _
            "Strain at UTS - measure of scaffold extensibility.", _
        "20% Secant Modulus E_sec (MPa)", _
            "stress(20%) / 0.20. Standard for flexible TPEs (ASTM D882).", _
        "Tangent Modulus at Break E_t (MPa)", _
            "Local OLS slope of the stress-strain curve at the fracture point (window = +/- " & TANGENT_WINDOW & " pts).", _
        "Toughness (MJ/m3)", _
            "Area under stress-strain curve up to UTS via trapezoidal rule. 1 MPa x strain fraction = 1 MJ/m3.", _
        "Anisotropy Ratio (AR)", _
            "AR = property(C) / property(L). AR > 1 means circumferentially dominant (fibre alignment).", _
        "Load at UTS (N)", _
            "Raw peak force - useful cross-check against load cell capacity.", _
        "Recommended additional tests", _
            "Biaxial testing, cyclic/fatigue, stress relaxation, Poisson ratio (DIC), strain energy density." _
    )

    For ni = 0 To UBound(notes) - 1 Step 2
        ws.Cells(sr, 1).Value = notes(ni)
        ws.Cells(sr, 1).Font.Bold = True
        ws.Range(ws.Cells(sr, 2), ws.Cells(sr, 8)).Merge
        ws.Cells(sr, 2).Value = notes(ni + 1)
        ws.Cells(sr, 2).WrapText = True
        ws.Rows(sr).RowHeight = 30
        If (ni \ 2) Mod 2 = 0 Then
            ws.Range(ws.Cells(sr, 1), ws.Cells(sr, 8)).Interior.Color = COL_ROW_ALT
        End If
        sr = sr + 1
    Next ni

    ws.Columns("A:N").AutoFit
    ws.Columns("A").ColumnWidth = 22
    ws.Columns("B").ColumnWidth = 18
End Sub

' ============================================================
' MATHS
' ============================================================
Function FindPeak(arSig() As Double, nr As Long) As Long
    Dim j   As Long
    Dim mx  As Double
    Dim idx As Long
    mx = -1E+308
    idx = 0
    For j = 0 To nr - 1
        If arSig(j) > mx Then
            mx = arSig(j)
            idx = j
        End If
    Next j
    FindPeak = idx
End Function

Function CalcSecant(arS() As Double, arSig() As Double, nr As Long, _
                    targetPct As Double) As Double
    Dim j   As Long
    Dim t   As Double
    Dim sat As Double
    CalcSecant = 0
    For j = 1 To nr - 1
        If arS(j - 1) <= targetPct And arS(j) >= targetPct Then
            If (arS(j) - arS(j - 1)) <> 0 Then
                t = (targetPct - arS(j - 1)) / (arS(j) - arS(j - 1))
            Else
                t = 0
            End If
            sat = arSig(j - 1) + t * (arSig(j) - arSig(j - 1))
            CalcSecant = sat / (targetPct / 100)
            Exit Function
        End If
    Next j
    If nr >= 2 And arS(nr - 1) > 0 Then
        CalcSecant = arSig(nr - 1) / (arS(nr - 1) / 100)
    End If
End Function

Function CalcTangent(arS() As Double, arSig() As Double, nr As Long, _
                     win As Integer) As Double
    Dim fracIdx As Long
    Dim lo      As Long
    Dim hi      As Long
    Dim nn      As Long
    Dim j       As Long
    Dim xv      As Double
    Dim yv      As Double
    Dim sx      As Double
    Dim sy      As Double
    Dim sxy     As Double
    Dim sx2     As Double
    Dim den     As Double

    CalcTangent = 0
    fracIdx = nr - 1
    lo = fracIdx - win
    If lo < 0 Then lo = 0
    hi = fracIdx + win
    If hi > nr - 1 Then hi = nr - 1
    nn = hi - lo + 1
    If nn < 2 Then Exit Function

    sx = 0: sy = 0: sxy = 0: sx2 = 0
    For j = lo To hi
        xv = arS(j) / 100
        yv = arSig(j)
        sx = sx + xv
        sy = sy + yv
        sxy = sxy + xv * yv
        sx2 = sx2 + xv * xv
    Next j

    den = nn * sx2 - sx * sx
    If Abs(den) < 1E-15 Then Exit Function
    CalcTangent = (nn * sxy - sx * sy) / den
End Function

Function CalcTough(arS() As Double, arSig() As Double, endIdx As Long) As Double
    Dim j      As Long
    Dim dEps   As Double
    Dim avgSig As Double
    CalcTough = 0
    For j = 1 To endIdx
        dEps = (arS(j) - arS(j - 1)) / 100
        avgSig = (arSig(j) + arSig(j - 1)) / 2
        CalcTough = CalcTough + avgSig * dEps
    Next j
End Function

Sub CalcMeanSD(vals() As Double, nVals As Integer, _
               ByRef mu As Double, ByRef sd As Double)
    Dim i  As Integer
    Dim ss As Double
    mu = 0
    sd = 0
    If nVals = 0 Then Exit Sub
    For i = 0 To nVals - 1
        mu = mu + vals(i)
    Next i
    mu = mu / nVals
    If nVals < 2 Then Exit Sub
    ss = 0
    For i = 0 To nVals - 1
        ss = ss + (vals(i) - mu) ^ 2
    Next i
    sd = Sqr(ss / (nVals - 1))
End Sub

' ============================================================
' FILENAME PARSING: p16f4c1 -> PEL=16 FR=4 Orient=C Rep=1
' ============================================================
Sub ParseName(fname As String, ByRef rs As TSpec)
    Dim bn     As String
    Dim pPos   As Integer
    Dim fPos   As Integer
    Dim k      As Integer
    Dim dc     As String
    Dim rstr   As String
    Dim ri     As Integer
    Dim repStr As String

    rs.sFile = fname
    rs.bValid = False

    bn = LCase(fname)
    If InStr(bn, ".") > 0 Then bn = Left(bn, InStrRev(bn, ".") - 1)
    rs.sName = bn

    pPos = InStr(bn, "p")
    fPos = InStr(bn, "f")
    If pPos > 0 And fPos > pPos Then
        rs.sPEL = Mid(bn, pPos + 1, fPos - pPos - 1)
    End If

    If fPos > 0 Then
        k = fPos + 1
        Do While k <= Len(bn)
            If Mid(bn, k, 1) >= "0" And Mid(bn, k, 1) <= "9" Then
                k = k + 1
            Else
                Exit Do
            End If
        Loop
        rs.sFR = Mid(bn, fPos + 1, k - fPos - 1)

        If k <= Len(bn) Then
            dc = Mid(bn, k, 1)
            If dc = "c" Then
                rs.sOrient = "C"
            ElseIf dc = "l" Then
                rs.sOrient = "L"
            Else
                rs.sOrient = "?"
            End If

            If k + 1 <= Len(bn) Then
                rstr = Mid(bn, k + 1)
                ri = 1
                Do While ri <= Len(rstr)
                    If Mid(rstr, ri, 1) >= "0" And Mid(rstr, ri, 1) <= "9" Then
                        ri = ri + 1
                    Else
                        Exit Do
                    End If
                Loop
                repStr = Left(rstr, ri - 1)
                If IsNumeric(repStr) Then rs.iRep = CInt(repStr)
            End If
        End If
    End If

    rs.sGroupID = "p" & rs.sPEL & "f" & rs.sFR

    Select Case rs.sPEL
        Case "16": rs.dThick = THICKNESS_P16
        Case "18": rs.dThick = THICKNESS_P18
        Case "20": rs.dThick = THICKNESS_P20
        Case Else: rs.dThick = THICKNESS_P18
    End Select

    rs.dArea = DOGBONE_WIDTH_MM * rs.dThick
End Sub

' Helper: convert C/L code to full label
Function OrientLabel(code As String) As String
    If code = "C" Then
        OrientLabel = "Circumferential"
    ElseIf code = "L" Then
        OrientLabel = "Longitudinal"
    Else
        OrientLabel = "Unknown"
    End If
End Function

' ============================================================
' SORT (bubble) by Group > Orient > Rep
' ============================================================
Sub SortRes(res() As TSpec, n As Integer)
    Dim i   As Integer
    Dim j   As Integer
    Dim tmp As TSpec
    Dim k1  As String
    Dim k2  As String
    For i = 0 To n - 2
        For j = 0 To n - 2 - i
            k1 = SortKey(res(j))
            k2 = SortKey(res(j + 1))
            If k1 > k2 Then
                tmp = res(j)
                res(j) = res(j + 1)
                res(j + 1) = tmp
            End If
        Next j
    Next i
End Sub

Function SortKey(rs As TSpec) As String
    Dim d As String
    If rs.sOrient = "C" Then d = "0" Else d = "1"
    SortKey = rs.sGroupID & d & Format(rs.iRep, "00")
End Function

' ============================================================
' CSV PARSER  (dynamic array; quoted fields)
' ============================================================
Function SplitCSV(lineTxt As String) As String()
    Dim flds() As String
    Dim fc     As Integer
    Dim cur    As String
    Dim inQ    As Boolean
    Dim i      As Integer
    Dim ch     As String

    ReDim flds(500)
    fc = 0
    cur = ""
    inQ = False

    For i = 1 To Len(lineTxt)
        ch = Mid(lineTxt, i, 1)
        If ch = """" Then
            inQ = Not inQ
        ElseIf ch = "," And Not inQ Then
            flds(fc) = Trim(cur)
            fc = fc + 1
            cur = ""
        Else
            cur = cur & ch
        End If
    Next i
    flds(fc) = Trim(cur)
    fc = fc + 1

    ReDim Preserve flds(fc - 1)
    SplitCSV = flds
End Function

Function GetField(flds() As String, idx As Integer) As String
    If idx >= 0 And idx <= UBound(flds) Then
        GetField = flds(idx)
    Else
        GetField = "0"
    End If
End Function

' ============================================================
' STYLE HELPERS  (use "rng" not "cell" to avoid Excel ambiguity)
' ============================================================
Sub StyleTitle(rng As Range)
    rng.Font.Bold = True
    rng.Font.Size = 14
    rng.Font.Name = "Arial"
    rng.Font.Color = RGB(26, 82, 118)
End Sub

Sub StyleSection(rng As Range)
    rng.Font.Bold = True
    rng.Font.Size = 11
    rng.Font.Name = "Arial"
    rng.Font.Color = RGB(255, 255, 255)
    rng.Interior.Color = RGB(26, 82, 118)
    rng.EntireRow.RowHeight = 22
End Sub

Sub StyleColHdr(rng As Range)
    rng.Font.Bold = True
    rng.Font.Size = 10
    rng.Font.Name = "Arial"
    rng.Font.Color = RGB(255, 255, 255)
    rng.Interior.Color = RGB(52, 120, 180)
    rng.HorizontalAlignment = xlCenter
    rng.VerticalAlignment = xlCenter
    rng.WrapText = True
End Sub
