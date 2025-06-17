document.addEventListener('DOMContentLoaded', function() {
    // Skill management
    document.querySelectorAll('.add-skill').forEach(button => {
        button.addEventListener('click', function() {
            const skillType = this.dataset.skillType;
            const input = this.previousElementSibling;
            const skillValue = input.value.trim();
            
            if (skillValue) {
                const container = document.getElementById(`${skillType}-skills-container`);
                
                // Create skill tag
                const tag = document.createElement('span');
                tag.className = 'skill-tag';
                tag.innerHTML = `
                    ${skillValue}
                    <input type="hidden" name="${skillType}_skills[]" value="${skillValue}">
                    <button type="button" class="remove-skill">
                        <i class="fas fa-times"></i>
                    </button>
                `;
                
                container.appendChild(tag);
                input.value = '';
                
                // Add remove functionality
                tag.querySelector('.remove-skill').addEventListener('click', function() {
                    tag.remove();
                });
            }
        });
    });
    
    // Language management
    const addLanguageBtn = document.querySelector('.add-language');
    if (addLanguageBtn) {
        addLanguageBtn.addEventListener('click', function() {
            const nameInput = document.querySelector('.language-name');
            const levelSelect = document.querySelector('.language-level');
            const container = document.getElementById('languages-container');
            
            const name = nameInput.value.trim();
            const level = levelSelect.value;
            
            if (name && level) {
                const tag = document.createElement('span');
                tag.className = 'language-tag';
                tag.innerHTML = `
                    ${name} (${level})
                    <input type="hidden" name="language_name[]" value="${name}">
                    <input type="hidden" name="language_level[]" value="${level}">
                    <button type="button" class="remove-skill">
                        <i class="fas fa-times"></i>
                    </button>
                `;
                
                container.appendChild(tag);
                nameInput.value = '';
                levelSelect.value = '';
                
                tag.querySelector('.remove-skill').addEventListener('click', function() {
                    tag.remove();
                });
            }
        });
    }
});