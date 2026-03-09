const fileInput = document.getElementById('fileInput');
const fileNameDisplay = document.getElementById('fileName');
const extractBtn = document.getElementById('extractBtn');
const resultContainer = document.getElementById('resultContainer');
const jsonOutput = document.getElementById('jsonOutput');
const statusDiv = document.getElementById('status');

const copyBtn = document.getElementById('copyBtn');
const downloadBtn = document.getElementById('downloadBtn');
const downloadExcelBtn = document.getElementById('downloadExcelBtn');
const confidenceBadge = document.getElementById('confidenceBadge');
const confidenceValue = document.getElementById('confidenceValue');

let lastExtractionData = null;

// Show selected filename
fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
        fileNameDisplay.textContent = fileInput.files[0].name;
        fileNameDisplay.style.color = 'var(--text-primary)';
    } else {
        fileNameDisplay.textContent = 'No file selected';
        fileNameDisplay.style.color = 'var(--text-secondary)';
    }
});

extractBtn.addEventListener('click', async () => {
    if (!fileInput.files[0]) {
        alert('Please select a file first.');
        return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);

    // Loading State
    extractBtn.disabled = true;
    extractBtn.textContent = 'Extracting...';
    statusDiv.textContent = '⏳ Initializing OCR engine...';
    resultContainer.classList.add('hidden');
    confidenceBadge.classList.add('hidden');
    jsonOutput.textContent = '';
    lastExtractionData = null;

    try {
        const response = await fetch('/extract', {
            method: 'POST',

            body: formData
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || `Error: ${response.statusText}`);
        }

        const data = await response.json();
        lastExtractionData = data;

        statusDiv.textContent = 'Done!';

        // Show Confidence
        if (data.overall_confidence !== undefined) {
            const percentage = (data.overall_confidence * 100).toFixed(1) + '%';
            confidenceValue.textContent = percentage;
            confidenceBadge.classList.remove('hidden');
        }

        // --- Populate Parsed Results ---
        const candidateGrid = document.getElementById('candidateGrid');
        const marksBody = document.getElementById('marksBody');

        // Clear previous
        candidateGrid.innerHTML = '';
        marksBody.innerHTML = '';

        // Helper function to safely get value from the nested {value: "...", confidence: ...} structure
        const getValue = (field) => {
            if (field && typeof field === 'object' && field.value !== undefined) {
                return field.value || '-';
            }
            return field || '-';
        };

        // 1. Candidate Details
        if (data.candidate_details) {
            for (const [key, fieldData] of Object.entries(data.candidate_details)) {
                const displayValue = getValue(fieldData);
                // Only show fields that have a value
                if (displayValue !== '-' && displayValue !== null) {
                    const item = document.createElement('div');
                    item.className = 'info-item';
                    item.innerHTML = `
                        <span class="info-label">${key.replace(/_/g, ' ')}</span>
                        <span class="info-value">${displayValue}</span>
                    `;
                    candidateGrid.appendChild(item);
                }
            }
        }

        // 2. Marks Table - Handle both Marksheet (subjects) and Exam Sheet (Part A/B) formats
        let subjects = [];
        const marksTableSection = document.getElementById('marksSection');
        
        // Check if it's an exam sheet with Part A and Part B
        if (data.exam_marks && (data.exam_marks.part_a || data.exam_marks.part_b)) {
            // Make sure marksSection exists and show it
            if (marksTableSection) marksTableSection.style.display = 'block';
            
            // Clear previous content
            marksBody.innerHTML = '';
            
            // Helper function for exam questions
            const displayExamMarks = (part, partName) => {
                if (!part || !part.questions) return;
                
                const partHeader = document.createElement('tr');
                partHeader.innerHTML = `<td colspan="3" style="background-color: #f0f0f0; font-weight: bold; text-align: center;">${partName} (Max: ${getValue(part.max_marks)})</td>`;
                marksBody.appendChild(partHeader);
                
                part.questions.forEach(q => {
                    const row = document.createElement('tr');
                    const qNo = getValue(q.question_no);
                    const maxM = getValue(q.max_marks);
                    const obtM = getValue(q.obtained_marks);
                    
                    row.innerHTML = `
                        <td>Q${qNo}</td>
                        <td>${obtM} / ${maxM}</td>
                        <td>-</td>
                    `;
                    marksBody.appendChild(row);
                });
            };
            
            displayExamMarks(data.exam_marks.part_a, 'PART-A');
            displayExamMarks(data.exam_marks.part_b, 'PART-B');
            
            // Show totals
            if (data.exam_totals) {
                const totalRow = document.createElement('tr');
                const ptA = getValue(data.exam_totals.part_a_total) || '-';
                const ptB = getValue(data.exam_totals.part_b_total) || '-';
                const grand = getValue(data.exam_totals.grand_total) || '-';
                
                totalRow.innerHTML = `
                    <td><strong>TOTALS</strong></td>
                    <td><strong>${grand} / ${getValue(data.exam_totals.max_marks)}</strong></td>
                    <td><strong>Part-A: ${ptA}, Part-B: ${ptB}</strong></td>
                `;
                totalRow.style.backgroundColor = '#e8f4f8';
                marksBody.appendChild(totalRow);
            }
            
        } else if (data.academic_details && Array.isArray(data.academic_details.subjects)) {
            // Original marksheet format with subjects
            if (marksTableSection) marksTableSection.style.display = 'block';
            
            subjects = data.academic_details.subjects;
            
            subjects.forEach(sub => {
                const row = document.createElement('tr');

                // Extract values using the helper
                const name = getValue(sub.subject);
                const marks = getValue(sub.obtained_marks);
                const max = getValue(sub.max_marks);
                const grade = getValue(sub.grade);

                // Construct marks display (e.g. "80 / 100")
                const marksDisplay = (max !== '-') ? `${marks} / ${max}` : marks;

                row.innerHTML = `
                    <td>${name}</td>
                    <td>${marksDisplay}</td>
                    <td>${grade}</td>
                `;
                marksBody.appendChild(row);
            });
        } else {
            marksBody.innerHTML = '<tr><td colspan="3" style="text-align:center; color:var(--text-secondary);">No marks data found.</td></tr>';
        }

        // Pretty print JSON
        jsonOutput.textContent = JSON.stringify(data, null, 2);
        resultContainer.classList.remove('hidden');

    } catch (error) {
        statusDiv.textContent = 'Failed to extract.';
        console.error(error);
        alert('An error occurred: ' + error.message);
    } finally {
        extractBtn.disabled = false;
        extractBtn.textContent = 'Extract Information';
    }
});

// Copy Feature
copyBtn.addEventListener('click', () => {
    if (!lastExtractionData) return;
    navigator.clipboard.writeText(JSON.stringify(lastExtractionData, null, 2));
    const originalText = copyBtn.textContent;
    copyBtn.textContent = '✅ Copied';
    setTimeout(() => copyBtn.textContent = originalText, 2000);
});

// Download Feature
downloadBtn.addEventListener('click', () => {
    if (!lastExtractionData) return;
    const blob = new Blob([JSON.stringify(lastExtractionData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'marksheet_data.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
});
// Download Excel Feature
downloadExcelBtn.addEventListener('click', async () => {
    if (!lastExtractionData) return;
    
    try {
        downloadExcelBtn.disabled = true;
        downloadExcelBtn.textContent = '⏳ Generating...';
        
        const response = await fetch('/export-excel', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(lastExtractionData)
        });
        
        if (!response.ok) {
            throw new Error(`Failed to generate Excel: ${response.statusText}`);
        }
        
        // Get the file blob
        const blob = await response.blob();
        
        // Create download link
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'marksheet_data.xlsx';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        downloadExcelBtn.textContent = '✅ Excel Downloaded';
        setTimeout(() => {
            downloadExcelBtn.textContent = '📊 Download Excel';
            downloadExcelBtn.disabled = false;
        }, 2000);
        
    } catch (error) {
        console.error('Excel download error:', error);
        alert('Failed to download Excel: ' + error.message);
        downloadExcelBtn.textContent = '📊 Download Excel';
        downloadExcelBtn.disabled = false;
    }
});