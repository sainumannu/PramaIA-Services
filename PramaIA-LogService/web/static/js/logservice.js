/**
 * Script per la pagina LogService
 * 
 * Gestisce l'interazione con la tab dedicata al LogService
 */

document.addEventListener('DOMContentLoaded', function() {
    // Gestione tab
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Rimuovi classe active da tutti i bottoni e pannelli
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabPanes.forEach(pane => pane.classList.remove('active'));
            
            // Aggiungi classe active al bottone cliccato
            this.classList.add('active');
            
            // Mostra il pannello corrispondente
            const tabId = this.dataset.tab;
            document.getElementById(tabId).classList.add('active');
        });
    });
});
