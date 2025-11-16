document.addEventListener('DOMContentLoaded', function() {
    const config = window.WORDSEARCH_CONFIG;
    let selectedCells = [];
    let foundWords = new Set();
    let currentPlayer = 1;
    
    initializeBoard();
    
    function initializeBoard() {
        const board = document.getElementById('ws-board');
        const cells = board.querySelectorAll('.ws-cell');
        
        cells.forEach(cell => {
            cell.addEventListener('mousedown', startSelection);
            cell.addEventListener('mouseenter', continueSelection);
            cell.addEventListener('touchstart', handleTouchStart);
        });
        
        document.addEventListener('mouseup', endSelection);
        document.addEventListener('touchend', endSelection);
        document.getElementById('ws-reset').addEventListener('click', resetSelection);
        updateProgress();
    }
    
    function startSelection(e) {
        e.preventDefault();
        selectedCells = [this];
        this.classList.add('selected', `player${currentPlayer}`);
        document.addEventListener('mousemove', preventDrag);
    }
    
    function continueSelection(e) {
        if (selectedCells.length === 0) return;
        
        const cell = this;
        const lastCell = selectedCells[selectedCells.length - 1];
        
        if (isAdjacent(lastCell, cell) && !selectedCells.includes(cell)) {
            selectedCells.push(cell);
            cell.classList.add('selected', `player${currentPlayer}`);
        }
    }
    
    function endSelection() {
        document.removeEventListener('mousemove', preventDrag);
        
        if (selectedCells.length > 1) {
            validateSelection();
        }
        
        setTimeout(() => {
            selectedCells.forEach(cell => {
                cell.classList.remove('selected', 'player1', 'player2');
            });
            selectedCells = [];
        }, 1000);
    }
    
    function validateSelection() {
        const positions = selectedCells.map(cell => [
            parseInt(cell.dataset.row),
            parseInt(cell.dataset.col)
        ]);
        
        for (const [word, wordPositions] of Object.entries(config.POSICIONES_PALABRAS)) {
            const positionsStr = JSON.stringify(positions);
            const wordPositionsStr = JSON.stringify(wordPositions);
            const reversedStr = JSON.stringify([...positions].reverse());
            
            if (positionsStr === wordPositionsStr || reversedStr === wordPositionsStr) {
                markWordAsFound(word, positions);
                break;
            }
        }
    }
    
    function markWordAsFound(word, positions) {
        if (foundWords.has(word)) return;
        
        foundWords.add(word);
        
        positions.forEach(([row, col]) => {
            const cell = document.querySelector(`.ws-cell[data-row="${row}"][data-col="${col}"]`);
            cell.classList.add('found', `found-player${currentPlayer}`);
        });
        
        const wordElement = document.getElementById(`word-${Array.from(foundWords).length}`);
        if (wordElement) {
            wordElement.classList.add('found');
        }
        
        updateProgress();
        
        currentPlayer = currentPlayer === 1 ? 2 : 1;
        
        if (foundWords.size === config.PALABRAS.length) {
            showCompletionModal();
        }
    }
    
    function updateProgress() {
        const progress = (foundWords.size / config.PALABRAS.length) * 100;
        const progressElement = document.getElementById('ws-progress-text');
        const countElement = document.getElementById('ws-found-count');
        
        if (progressElement) {
            progressElement.textContent = `${Math.round(progress)}%`;
        }
        if (countElement) {
            countElement.textContent = `${foundWords.size}/${config.PALABRAS.length} encontradas`;
        }
    }
    
    function resetSelection() {
        selectedCells.forEach(cell => {
            cell.classList.remove('selected', 'player1', 'player2');
        });
        selectedCells = [];
    }
    
    function showCompletionModal() {
        const modal = document.getElementById('ws-complete');
        modal.hidden = false;
        
        fetch('/api/etapa1-completada/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': config.CSRF_TOKEN
            },
            body: JSON.stringify({ completado: true })
        });
    }
    
    function isAdjacent(cell1, cell2) {
        const row1 = parseInt(cell1.dataset.row);
        const col1 = parseInt(cell1.dataset.col);
        const row2 = parseInt(cell2.dataset.row);
        const col2 = parseInt(cell2.dataset.col);
        
        const rowDiff = Math.abs(row1 - row2);
        const colDiff = Math.abs(col1 - col2);
        
        return (rowDiff <= 1 && colDiff <= 1) && (rowDiff + colDiff > 0);
    }
    
    function preventDrag(e) {
        e.preventDefault();
    }
    
    function handleTouchStart(e) {
        e.preventDefault();
        startSelection.call(this, e);
    }
});