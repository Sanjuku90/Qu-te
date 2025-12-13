function completeQuest(questId) {
    const button = event.target;
    button.disabled = true;
    button.textContent = 'En cours...';
    
    fetch(`/complete_quest/${questId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const questCard = document.getElementById(`quest-${questId}`);
            questCard.classList.add('completed');
            button.textContent = 'Complétée ✓';
            button.classList.remove('btn-primary');
            button.classList.add('btn-disabled');
            
            document.getElementById('current-balance').textContent = data.new_balance.toFixed(2) + '€';
            document.getElementById('completed-count').textContent = data.completed_today + '/4';
            
            const balanceDisplay = document.querySelector('.balance-display');
            if (balanceDisplay) {
                balanceDisplay.textContent = 'Solde: ' + data.new_balance.toFixed(2) + '€';
            }
            
            showNotification(data.message, 'success');
        } else {
            button.disabled = false;
            button.textContent = 'Compléter la quête';
            showNotification(data.message, 'error');
        }
    })
    .catch(error => {
        button.disabled = false;
        button.textContent = 'Compléter la quête';
        showNotification('Une erreur est survenue', 'error');
    });
}

function toggleWithdraw() {
    const form = document.getElementById('withdraw-form');
    form.style.display = form.style.display === 'none' ? 'block' : 'none';
}

function showNotification(message, type) {
    const existing = document.querySelector('.notification');
    if (existing) existing.remove();
    
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        padding: 1rem 2rem;
        border-radius: 8px;
        z-index: 1000;
        animation: slideIn 0.3s ease;
        background: ${type === 'success' ? '#22c55e' : '#ef4444'};
        color: white;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);
