/**
 * File Parsing Processor - PDK Implementation  
 * Estrae testo da file PDF usando PyPDF2/pdfplumber via Python child process
 */

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

class FileParsingProcessor {
    constructor() {
        this.name = 'File Parsing Processor';
        this.description = 'Estrazione testo da PDF con PyPDF2 e pdfplumber';
        this.supportedFormats = ['.pdf'];
        this.maxFileSize = 50 * 1024 * 1024; // 50MB
    }

    async execute(input, config, context) {
        const logger = context.logger || console;
        
        logger.info(`📄 File Parsing Processor: processing file`);
        
        const filePath = input.file_path;
        if (!filePath) {
            throw new Error('file_path richiesto per il parsing');
        }

        // Validazione file
        if (!fs.existsSync(filePath)) {
            throw new Error(`File non trovato: ${filePath}`);
        }

        const fileExtension = path.extname(filePath).toLowerCase();
        if (!this.supportedFormats.includes(fileExtension)) {
            throw new Error(`Formato file non supportato: ${fileExtension}`);
        }

        // Controllo dimensione
        const stats = fs.statSync(filePath);
        const maxSize = config.max_file_size_mb ? config.max_file_size_mb * 1024 * 1024 : this.maxFileSize;
        if (stats.size > maxSize) {
            throw new Error(`File troppo grande: ${stats.size} bytes`);
        }

        // Estrazione contenuto via Python
        const extractionResult = await this._extractPdfContent(filePath, logger);
        
        // Aggiungi informazioni file
        extractionResult.file_info = {
            file_path: filePath,
            file_name: path.basename(filePath),
            file_size: stats.size,
            file_extension: fileExtension,
            processing_timestamp: new Date().toISOString()
        };

        logger.info(`✅ File processato: ${extractionResult.text?.length || 0} caratteri estratti`);
        return extractionResult;
    }

    async _extractPdfContent(filePath, logger) {
        return new Promise((resolve, reject) => {
            // Script Python per estrazione PDF
            const pythonScript = `
import sys
import json
import PyPDF2
import pdfplumber
import re
from pathlib import Path

def extract_pdf_content(file_path):
    text_content = ""
    metadata = {}
    pages_info = []
    
    try:
        # PyPDF2 per metadati
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            if pdf_reader.metadata:
                metadata.update({
                    "title": str(pdf_reader.metadata.get("/Title", "")),
                    "author": str(pdf_reader.metadata.get("/Author", "")),
                    "subject": str(pdf_reader.metadata.get("/Subject", "")),
                    "creator": str(pdf_reader.metadata.get("/Creator", "")),
                    "producer": str(pdf_reader.metadata.get("/Producer", "")),
                })
            
            metadata["pages"] = len(pdf_reader.pages)
            
            # Estrazione testo PyPDF2
            pypdf2_text = ""
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    pypdf2_text += page_text + "\\n"
                    pages_info.append({
                        "page_number": page_num + 1,
                        "text_length": len(page_text),
                        "extraction_method": "PyPDF2"
                    })
                except:
                    pass
    except Exception as e:
        pypdf2_text = ""
    
    try:
        # pdfplumber per testo più accurato
        with pdfplumber.open(file_path) as pdf:
            pdfplumber_text = ""
            
            for page_num, page in enumerate(pdf.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        pdfplumber_text += page_text + "\\n"
                        if page_num < len(pages_info):
                            pages_info[page_num]["pdfplumber_length"] = len(page_text)
                except:
                    pass
    except Exception as e:
        pdfplumber_text = ""
    
    # Scegli il testo migliore
    if len(pdfplumber_text.strip()) > len(pypdf2_text.strip()):
        text_content = pdfplumber_text
        extraction_method = "pdfplumber"
    else:
        text_content = pypdf2_text
        extraction_method = "PyPDF2"
    
    # Pulizia testo
    text_content = re.sub(r'[\\x00-\\x08\\x0B\\x0C\\x0E-\\x1F\\x7F-\\x9F]', '', text_content)
    text_content = re.sub(r' +', ' ', text_content)
    text_content = re.sub(r'\\n\\s*\\n', '\\n\\n', text_content)
    text_content = text_content.strip()
    
    return {
        "text": text_content,
        "metadata": metadata,
        "pages_info": pages_info,
        "extraction_method": extraction_method,
        "extraction_status": "success" if text_content else "no_text_extracted"
    }

if __name__ == "__main__":
    file_path = sys.argv[1]
    result = extract_pdf_content(file_path)
    print(json.dumps(result, ensure_ascii=False))
`;

            // Scrivi script temporaneo
            const tempScript = path.join(__dirname, 'temp_pdf_extract.py');
            fs.writeFileSync(tempScript, pythonScript);

            // Esegui Python
            const python = spawn('python', [tempScript, filePath]);
            
            let stdout = '';
            let stderr = '';

            python.stdout.on('data', (data) => {
                stdout += data.toString();
            });

            python.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            python.on('close', (code) => {
                // Pulisci script temporaneo
                try {
                    fs.unlinkSync(tempScript);
                } catch (e) {
                    logger.warn(`Impossibile rimuovere script temporaneo: ${e.message}`);
                }

                if (code !== 0) {
                    reject(new Error(`Python script failed: ${stderr}`));
                    return;
                }

                try {
                    const result = JSON.parse(stdout);
                    resolve(result);
                } catch (e) {
                    reject(new Error(`Failed to parse Python output: ${e.message}`));
                }
            });

            python.on('error', (error) => {
                reject(new Error(`Failed to start Python process: ${error.message}`));
            });
        });
    }

    validate(config) {
        if (config.max_file_size_mb && (typeof config.max_file_size_mb !== 'number' || config.max_file_size_mb <= 0)) {
            return { valid: false, error: 'max_file_size_mb deve essere un numero positivo' };
        }
        return { valid: true };
    }
}

module.exports = FileParsingProcessor;