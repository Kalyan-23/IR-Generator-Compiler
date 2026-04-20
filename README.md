# 🚀 IR-Generator-Compiler

> A complete **Intermediate Code Generator Toolkit** for Compiler Design that transforms high-level expressions into machine-independent representations.

---

## 📌 Overview

This project implements a full pipeline of a **compiler front-end**, converting source expressions into:

* ✅ Tokens (Lexical Analysis)
* ✅ Abstract Syntax Tree (AST)
* ✅ Postfix Notation (RPN)
* ✅ Three Address Code (TAC)

It also provides an **interactive UI using Streamlit** for visualization and step-by-step execution.

---

## ✨ Features

### 🔹 1. Lexical Analysis

* Converts source code into tokens using regex-based tokenizer
* Handles identifiers, numbers, operators, and syntax errors
---

### 🔹 2. Syntax Analysis (Parser + AST)

* Recursive-descent parser with operator precedence
* Supports:

  * Binary operations (+, -, *, /)
  * Unary operations (−)
  * Assignment statements
* Generates structured AST

---

### 🌳 3. AST Visualization

* Graphical tree using pure SVG (no external libraries)
* Color-coded nodes for better understanding
* Also provides text-based tree representation

---

### 🔁 4. Postfix Notation (RPN)

* Converts expressions into postfix format
* Provides **step-by-step execution**
* Useful for stack-based evaluation

---

### ⚙️ 5. Three Address Code (TAC)

Generates multiple intermediate representations:

* 📌 **Quadruples** → (op, arg1, arg2, result)
* 📌 **Triples** → indexed representation
* 📌 **Indirect Triples** → pointer-based structure

💡 Includes **Common Subexpression Elimination (CSE)** optimization

---

### 🖥️ 6. Interactive Web UI

* Built using **Streamlit**

* Sidebar navigation with multiple sections

* Features:

  * AST Visualization (SVG + Text)
  * Postfix Conversion (with steps)
  * TAC Generation (all formats)
  * Token Inspector

* Main app: 

---

## 🧠 Architecture

```
  Input Expression
       ↓
   Lexer (Tokens)
       ↓
   Parser (AST)
       ↓
 ┌───────────────┬───────────────┬───────────────┐
 │   AST View    │   Postfix     │      TAC      │
 │ (SVG + Text)  │   (RPN)       │ (3 Formats)   │
 └───────────────┴───────────────┴───────────────┘
```

---

## 📂 Project Structure

```
├── App.py              # Streamlit UI
├── Lexer.py           # Tokenizer
├── Parser.py          # Parser + AST
├── Postfix.py         # Postfix generator
├── Codegen.py         # TAC generator
├── ast_visual.py      # AST visualization (SVG)
```
---

## 🎯 Learning Outcomes

* Understanding of **compiler design phases**
* Implementation of:

  * Lexical analysis
  * Parsing techniques
  * AST construction
  * Intermediate code generation
* Exposure to **code optimization (CSE)**

---

## Screenshot
<img width="1904" height="934" alt="Screenshot 2026-04-20 102838" src="https://github.com/user-attachments/assets/cd2dae50-2af5-4f0f-8a6d-1193dd53f14a" />

---
## 🚀 Future Enhancements

* Code optimization techniques (Dead Code Elimination, Constant Folding)
* Support for control flow statements (if, while)
* Assembly code generation
* Export results as PDF/Excel
