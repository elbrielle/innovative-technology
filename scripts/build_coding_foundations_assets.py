#!/usr/bin/env python3
"""Build the bilingual student artifacts for the coding-foundations retrofit.

These files are staging assets for Google Docs and Canvas. Canvas remains the
curriculum source after the artifacts are uploaded and linked by immutable IDs.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


INK = "000000"
MUTED = "555555"
BORDER = "DADCE0"
LIGHT = "F8F9FA"
ACCENT = "0E7C7B"
CONTENT_WIDTH_DXA = 9360


def set_font(run, name: str = "Arial", size: float = 11, bold: bool = False, color: str = INK):
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), name)
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), name)
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = RGBColor.from_string(color)


def set_cell_margins(cell, top=80, start=120, bottom=80, end=120):
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for side, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{side}"))
        if node is None:
            node = OxmlElement(f"w:{side}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_cell_shading(cell, fill: str):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_paragraph_box(paragraph, fill: str = LIGHT):
    p_pr = paragraph._p.get_or_add_pPr()
    shd = p_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        p_pr.append(shd)
    shd.set(qn("w:fill"), fill)
    borders = p_pr.find(qn("w:pBdr"))
    if borders is None:
        borders = OxmlElement("w:pBdr")
        p_pr.append(borders)
    for edge in ("top", "left", "bottom", "right"):
        node = borders.find(qn(f"w:{edge}"))
        if node is None:
            node = OxmlElement(f"w:{edge}")
            borders.append(node)
        node.set(qn("w:val"), "single")
        node.set(qn("w:sz"), "6")
        node.set(qn("w:space"), "5")
        node.set(qn("w:color"), BORDER)


def mark_header_row(row):
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def set_table_geometry(table, widths_dxa: list[int]):
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    table.autofit = False
    tbl_pr = table._tbl.tblPr
    tbl_w = tbl_pr.first_child_found_in("w:tblW")
    if tbl_w is None:
        tbl_w = OxmlElement("w:tblW")
        tbl_pr.append(tbl_w)
    tbl_w.set(qn("w:w"), str(sum(widths_dxa)))
    tbl_w.set(qn("w:type"), "dxa")
    tbl_ind = tbl_pr.first_child_found_in("w:tblInd")
    if tbl_ind is None:
        tbl_ind = OxmlElement("w:tblInd")
        tbl_pr.append(tbl_ind)
    tbl_ind.set(qn("w:w"), "0")
    tbl_ind.set(qn("w:type"), "dxa")
    grid = table._tbl.tblGrid
    for child in list(grid):
        grid.remove(child)
    for width in widths_dxa:
        col = OxmlElement("w:gridCol")
        col.set(qn("w:w"), str(width))
        grid.append(col)
    for row in table.rows:
        for index, cell in enumerate(row.cells):
            cell.width = Inches(widths_dxa[index] / 1440)
            tc_pr = cell._tc.get_or_add_tcPr()
            tc_w = tc_pr.first_child_found_in("w:tcW")
            tc_w.set(qn("w:w"), str(widths_dxa[index]))
            tc_w.set(qn("w:type"), "dxa")
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_margins(cell)


def style_document(doc: Document):
    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(0.65)
    section.bottom_margin = Inches(0.65)
    section.left_margin = Inches(0.75)
    section.right_margin = Inches(0.75)
    section.header_distance = Inches(0.3)
    section.footer_distance = Inches(0.3)

    normal = doc.styles["Normal"]
    normal.font.name = "Arial"
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Arial")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Arial")
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = RGBColor.from_string(INK)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.08

    for name, size, color, before, after in (
        ("Heading 1", 18, INK, 12, 5),
        ("Heading 2", 14, ACCENT, 10, 4),
        ("Heading 3", 12, MUTED, 8, 3),
    ):
        style = doc.styles[name]
        style.font.name = "Arial"
        style._element.rPr.rFonts.set(qn("w:ascii"), "Arial")
        style._element.rPr.rFonts.set(qn("w:hAnsi"), "Arial")
        style.font.size = Pt(size)
        style.font.color.rgb = RGBColor.from_string(color)
        style.font.bold = False
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)


def add_title(doc: Document, title: str, subtitle: str):
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(3)
    run = paragraph.add_run(title)
    set_font(run, size=24, bold=False)
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(10)
    run = paragraph.add_run(subtitle)
    set_font(run, size=10.5, color=MUTED)


def add_identity(doc: Document, labels: tuple[str, str, str]):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(7)
    p.paragraph_format.space_after = Pt(12)
    for index, label in enumerate(labels):
        if index:
            p.add_run("     ")
        set_font(p.add_run(f"{label}: "), bold=True)
        set_font(p.add_run("________________"), color=MUTED)


def add_instructions(doc: Document, heading: str, lines: list[str]):
    doc.add_heading(heading, level=2)
    for line in lines:
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.space_after = Pt(3)
        set_font(p.add_run(line))


def add_prompt(doc: Document, label: str, prompt: str, lines: int = 2):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(2)
    set_font(p.add_run(label + " "), bold=True, color=ACCENT)
    set_font(p.add_run(prompt))
    for _ in range(lines):
        p = doc.add_paragraph("________________________________________________________________________________")
        p.paragraph_format.space_after = Pt(3)
        set_font(p.runs[0], size=9, color=MUTED)


def add_code_box(doc: Document, title: str, code_lines: list[str]):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    set_font(p.add_run(title), bold=True, color=ACCENT)
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(0)
    paragraph.paragraph_format.left_indent = Inches(0.08)
    paragraph.paragraph_format.right_indent = Inches(0.08)
    set_paragraph_box(paragraph)
    for index, line in enumerate(code_lines):
        if index:
            paragraph.add_run("\n")
        set_font(paragraph.add_run(line), name="Courier New", size=9.5)


def add_variable_table(doc: Document, headers: list[str], rows: list[list[str]], row_lines: int = 1):
    table = doc.add_table(rows=1, cols=4)
    table.style = "Table Grid"
    set_table_geometry(table, [2300, 1700, 2300, 3060])
    mark_header_row(table.rows[0])
    for cell, value in zip(table.rows[0].cells, headers):
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_font(p.add_run(value), bold=True)
        set_cell_shading(cell, LIGHT)
    for row_values in rows:
        cells = table.add_row().cells
        for cell, value in zip(cells, row_values):
            set_font(cell.paragraphs[0].add_run(value + ("\n" * (row_lines - 1))))
    set_table_geometry(table, [2300, 1700, 2300, 3060])


def add_page_number(doc: Document):
    footer = doc.sections[0].footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    set_font(footer.add_run("Coding Foundations Passport"), size=8, color=MUTED)


def page_break(doc: Document):
    doc.add_page_break()


TEXT = {
    "en": {
        "title": "Coding Foundations Passport",
        "subtitle": "Use the same planning record as you move from spoken directions to blocks, games, text code, and robots.",
        "identity": ("Name", "Class", "Date started"),
        "how": "How this passport works",
        "how_lines": [
            "Complete only the checkpoint your teacher assigns today; keep the same passport for the whole coding sequence.",
            "Pseudocode is a precise human-readable plan. It is not tied to one programming language.",
            "Use short commands, indentation, meaningful variable names, and repeated steps that another person can follow literally.",
            "A screenshot proves that code ran. Your planning, test evidence, and explanation prove what you understand.",
        ],
        "c1": "Checkpoint 1 - Decompose and plan before blocks",
        "c1_context": "Current context: Code.org route or teacher-provided task",
        "c1_prompts": [
            ("Goal:", "What must the finished program make happen?", 2),
            ("Inputs and outputs:", "What information or action enters the system? What should the system produce?", 2),
            ("Subproblems:", "Break the goal into at least three smaller jobs.", 3),
        ],
        "pseudo_title": "First pseudocode draft",
        "pseudo_lines": ["START", "  [first precise command]", "  [next command]", "  [repeat or decision if needed]", "END"],
        "literal": "Partner literal test:",
        "literal_prompt": "Have a partner follow only what is written. Where did the plan become unclear or incomplete?",
        "c2": "Checkpoint 2 - Find patterns, variables, and abstraction",
        "pattern": [
            ("Repeated pattern:", "Which steps repeat? Describe the smallest useful repeated group.", 2),
            ("Iteration benefit:", "Why is a loop better here than copying the same commands?", 2),
            ("Generalize:", "Replace a task-specific detail with a variable or procedure so the plan can solve a similar problem.", 3),
        ],
        "var_headers": ["Variable name", "Data type", "Starting value", "Operation or change"],
        "var_rows": [["", "number / string / Boolean", "", ""], ["", "number / string / Boolean", "", ""], ["", "number / string / Boolean", "", ""]],
        "abstract_title": "Generalized pseudocode",
        "abstract_lines": ["SET [meaningful variable] TO [starting value]", "REPEAT [count or condition]", "  RUN [reusable procedure]", "END REPEAT"],
        "c3": "Checkpoint 3 - Predict, test, and improve",
        "test_headers": ["Prediction", "Observed result", "One change", "Result after change"],
        "test_rows": [["", "", "", ""], ["", "", "", ""], ["", "", "", ""]],
        "c3_prompts": [
            ("Pseudocode revision:", "Copy the exact line you changed and write the improved version.", 3),
            ("Improvement claim:", "The revision improved the algorithm because...", 2),
        ],
        "check_title": "Before submitting this checkpoint",
        "checks": [
            "I made a prediction before I ran the program.",
            "I changed only one instruction or value during each test.",
            "I revised the matching pseudocode, not only the executable code.",
            "My evidence names a cause, a result, and an improvement.",
        ],
        "c4": "Checkpoint 4 - Plan a game feature, then read text code",
        "c4_prompts": [
            ("Feature goal:", "Name one challenge, reward, rule, identity choice, feedback cue, or progression feature.", 2),
            ("Trigger and result:", "WHEN __________ happens, the program SHOULD __________.", 2),
            ("Feature pseudocode:", "Write the feature logic before changing the MakeCode project.", 4),
        ],
        "bridge": "Text-code bridge: Emergency Supply Grid",
        "bridge_lines": [
            "Open a new MakeCode Arcade project, name it Emergency Supply Grid, and select JavaScript.",
            "Trace the outer loop as rows and the inner loop as columns. One full inner loop completes one row.",
            "Use a string, numbers, and a Boolean. Perform addition, multiplication, comparison, and Boolean operations.",
            "Change the grid dimensions, predict the total, run the program, and record evidence.",
        ],
        "trace_headers": ["Code element", "What it stores or controls", "Predicted value", "Observed evidence"],
        "trace_rows": [["missionName", "", "", ""], ["rows / columns", "", "", ""], ["priorityMode", "", "", ""], ["suppliesPlaced", "", "", ""]],
        "c5": "Checkpoint 5 - Collaborate, execute literally, and revise for RVR",
        "collab_headers": ["Role", "Student", "Responsibility", "Evidence due"],
        "collab_rows": [["Planner", "", "", ""], ["Programmer", "", "", ""], ["Tester / evidence lead", "", "", ""]],
        "timeline_headers": ["Milestone", "Expected time", "Done?", "Adjustment"],
        "timeline_rows": [["Plan approved", "", "", ""], ["First run", "", "", ""], ["Revision run", "", "", ""]],
        "c5_prompts": [
            ("Robot pseudocode:", "Write the movement plan with headings, speed, duration/distance, waits, and repeated actions.", 5),
            ("Literal execution result:", "What did the robot or peer do when the plan was followed exactly?", 2),
            ("Final revision:", "What changed, what evidence justified it, and what improved?", 3),
        ],
        "final": "Final reflection",
        "final_prompt": "How did pseudocode help you move between a block program, a text program, and a robot program? Use one specific example.",
    },
    "es": {
        "title": "Pasaporte de Fundamentos de Programación",
        "subtitle": "Usa el mismo registro de planificación al pasar de instrucciones habladas a bloques, juegos, código de texto y robots.",
        "identity": ("Nombre", "Clase", "Fecha de inicio"),
        "how": "Cómo funciona este pasaporte",
        "how_lines": [
            "Completa solamente el punto de control que tu maestro asigne hoy; conserva el mismo pasaporte durante toda la secuencia.",
            "El pseudocódigo es un plan preciso y legible para personas. No pertenece a un solo lenguaje de programación.",
            "Usa comandos cortos, sangría, nombres de variables significativos y pasos repetidos que otra persona pueda seguir literalmente.",
            "Una captura demuestra que el código funcionó. Tu plan, pruebas y explicación demuestran lo que comprendes.",
        ],
        "c1": "Punto de control 1 - Descomponer y planear antes de usar bloques",
        "c1_context": "Contexto actual: ruta de Code.org o tarea proporcionada por el maestro",
        "c1_prompts": [
            ("Meta:", "¿Qué debe lograr el programa terminado?", 2),
            ("Entradas y salidas:", "¿Qué información o acción entra al sistema? ¿Qué debe producir el sistema?", 2),
            ("Subproblemas:", "Divide la meta en por lo menos tres trabajos más pequeños.", 3),
        ],
        "pseudo_title": "Primer borrador de pseudocódigo",
        "pseudo_lines": ["INICIO", "  [primer comando preciso]", "  [siguiente comando]", "  [repetición o decisión si es necesaria]", "FIN"],
        "literal": "Prueba literal con un compañero:",
        "literal_prompt": "Pide a un compañero que siga solamente lo escrito. ¿Dónde fue poco claro o incompleto el plan?",
        "c2": "Punto de control 2 - Encontrar patrones, variables y abstracción",
        "pattern": [
            ("Patrón repetido:", "¿Qué pasos se repiten? Describe el grupo repetido más pequeño y útil.", 2),
            ("Beneficio de la iteración:", "¿Por qué un bucle es mejor que copiar los mismos comandos?", 2),
            ("Generalizar:", "Reemplaza un detalle específico con una variable o procedimiento para resolver un problema parecido.", 3),
        ],
        "var_headers": ["Nombre de variable", "Tipo de dato", "Valor inicial", "Operacion o cambio"],
        "var_rows": [["", "número / texto / Booleano", "", ""], ["", "número / texto / Booleano", "", ""], ["", "número / texto / Booleano", "", ""]],
        "abstract_title": "Pseudocódigo generalizado",
        "abstract_lines": ["FIJAR [variable significativa] EN [valor inicial]", "REPETIR [cantidad o condición]", "  EJECUTAR [procedimiento reutilizable]", "FIN REPETIR"],
        "c3": "Punto de control 3 - Predecir, probar y mejorar",
        "test_headers": ["Prediccion", "Resultado observado", "Un cambio", "Resultado despues"],
        "test_rows": [["", "", "", ""], ["", "", "", ""], ["", "", "", ""]],
        "c3_prompts": [
            ("Revisión de pseudocódigo:", "Copia la línea exacta que cambiaste y escribe la versión mejorada.", 3),
            ("Afirmación de mejora:", "La revisión mejoró el algoritmo porque...", 2),
        ],
        "check_title": "Antes de entregar este punto de control",
        "checks": [
            "Hice una predicción antes de ejecutar el programa.",
            "Cambié solamente una instrucción o valor durante cada prueba.",
            "Revisé el pseudocódigo correspondiente, no solamente el código ejecutable.",
            "Mi evidencia nombra una causa, un resultado y una mejora.",
        ],
        "c4": "Punto de control 4 - Planear una funcion de juego y leer codigo de texto",
        "c4_prompts": [
            ("Meta de la función:", "Nombra un desafío, recompensa, regla, opción de identidad, aviso o progreso.", 2),
            ("Evento y resultado:", "CUANDO __________ ocurra, el programa DEBE __________.", 2),
            ("Pseudocódigo de la función:", "Escribe la lógica antes de cambiar el proyecto de MakeCode.", 4),
        ],
        "bridge": "Puente de código de texto: Cuadrícula de Suministros de Emergencia",
        "bridge_lines": [
            "Abre un proyecto nuevo de MakeCode Arcade, nómbralo Emergency Supply Grid y selecciona JavaScript.",
            "Sigue el bucle exterior como filas y el interior como columnas. Un bucle interior completo termina una fila.",
            "Usa texto, números y un Booleano. Realiza suma, multiplicación, comparación y operaciones Booleanas.",
            "Cambia las dimensiones, predice el total, ejecuta el programa y registra evidencia.",
        ],
        "trace_headers": ["Elemento de codigo", "Que guarda o controla", "Valor previsto", "Evidencia observada"],
        "trace_rows": [["missionName", "", "", ""], ["rows / columns", "", "", ""], ["priorityMode", "", "", ""], ["suppliesPlaced", "", "", ""]],
        "c5": "Punto de control 5 - Colaborar, ejecutar literalmente y revisar para RVR",
        "collab_headers": ["Rol", "Estudiante", "Responsabilidad", "Evidencia"],
        "collab_rows": [["Planificador", "", "", ""], ["Programador", "", "", ""], ["Pruebas / evidencia", "", "", ""]],
        "timeline_headers": ["Meta intermedia", "Tiempo previsto", "¿Listo?", "Ajuste"],
        "timeline_rows": [["Plan aprobado", "", "", ""], ["Primera prueba", "", "", ""], ["Prueba revisada", "", "", ""]],
        "c5_prompts": [
            ("Pseudocódigo del robot:", "Escribe movimientos con dirección, velocidad, duración/distancia, pausas y repeticiones.", 5),
            ("Resultado literal:", "¿Qué hizo el robot o compañero al seguir el plan exactamente?", 2),
            ("Revisión final:", "¿Qué cambió, qué evidencia lo justificó y qué mejoró?", 3),
        ],
        "final": "Reflexión final",
        "final_prompt": "¿Cómo te ayudó el pseudocódigo a pasar entre un programa de bloques, uno de texto y uno de robot? Usa un ejemplo específico.",
    },
}


def build(lang: str, output: Path):
    t = TEXT[lang]
    doc = Document()
    style_document(doc)
    add_title(doc, t["title"], t["subtitle"])
    add_identity(doc, t["identity"])
    add_instructions(doc, t["how"], t["how_lines"])
    doc.add_heading(t["c1"], level=1)
    p = doc.add_paragraph()
    set_font(p.add_run(t["c1_context"]), bold=True, color=MUTED)
    for label, prompt, lines in t["c1_prompts"]:
        add_prompt(doc, label, prompt, lines)
    add_code_box(doc, t["pseudo_title"], t["pseudo_lines"])
    add_prompt(doc, t["literal"], t["literal_prompt"], 2)

    page_break(doc)
    doc.add_heading(t["c2"], level=1)
    for label, prompt, lines in t["pattern"]:
        add_prompt(doc, label, prompt, lines)
    add_variable_table(doc, t["var_headers"], t["var_rows"])
    add_code_box(doc, t["abstract_title"], t["abstract_lines"])

    page_break(doc)
    doc.add_heading(t["c3"], level=1)
    add_variable_table(doc, t["test_headers"], t["test_rows"], row_lines=4)
    for label, prompt, lines in t["c3_prompts"]:
        add_prompt(doc, label, prompt, lines)
    add_instructions(doc, t["check_title"], t["checks"])

    page_break(doc)
    doc.add_heading(t["c4"], level=1)
    for label, prompt, lines in t["c4_prompts"]:
        add_prompt(doc, label, prompt, lines)
    doc.add_heading(t["bridge"], level=2)
    for line in t["bridge_lines"]:
        p = doc.add_paragraph(style="List Number")
        set_font(p.add_run(line))
    add_variable_table(doc, t["trace_headers"], t["trace_rows"])

    page_break(doc)
    doc.add_heading(t["c5"], level=1)
    add_variable_table(doc, t["collab_headers"], t["collab_rows"])
    doc.add_heading("Timeline" if lang == "en" else "Linea de tiempo", level=2)
    add_variable_table(doc, t["timeline_headers"], t["timeline_rows"])
    for label, prompt, lines in t["c5_prompts"]:
        add_prompt(doc, label, prompt, lines)
    doc.add_heading(t["final"], level=2)
    add_prompt(doc, "", t["final_prompt"], 3)
    add_page_number(doc)
    output.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    build("en", args.output_dir / "Coding_Foundations_Passport_EN.docx")
    build("es", args.output_dir / "Coding_Foundations_Passport_ES.docx")


if __name__ == "__main__":
    main()
