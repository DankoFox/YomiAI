# Skill: Academic LaTeX Review (/review-latex)

## Purpose
Act as a rigorous academic editor. Review the provided LaTeX text or `.tex` file and evaluate it against high academic standards. 

## Review Checklist
When triggered, output a structured review containing the following sections:

1. **Academic Tone & Clarity:** 
   - Identify any informal language, colloquialisms, or overly passive voice.
   - Suggest more precise academic vocabulary where appropriate.
2. **Structural Flow:** 
   - Check if paragraph transitions are logical. 
   - Ensure arguments are well-supported and not purely speculative.
3. **Citation & Evidence Gaps:** 
   - Identify strong claims that are missing citations.
   - Verify that all existing citations use the `\cite{}` format explicitly.
4. **LaTeX Syntax & Formatting:** 
   - Flag any unescaped special characters (like `&`, `%`, `$`).
   - Point out broken environments (e.g., mismatched `\begin` and `\end`).
   - Check for proper use of `\textbf{}`, `\textit{}`, and section headers.

## Output Format
Do NOT rewrite the entire text for the user unless specifically asked. Instead, provide a bulleted list of actionable critiques and isolated snippets of suggested corrections.
