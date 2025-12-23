document.addEventListener('DOMContentLoaded', () => {
    const search = document.getElementById('ask-tagsearch');
    const tagsContainer = document.getElementById('ask-tagchoices');
    const hiddenInput = document.getElementById('id_tags');
    let selectedTagIds = new Set();
    
    function updateHiddenInput() {
        hiddenInput.value = Array.from(selectedTagIds).join(',');
    }
    
    tagsContainer.addEventListener('click', e => {
        if (e.target.classList.contains('ask-tag')) {
            const tagId = e.target.getAttribute('data-tag-id');
            if (selectedTagIds.has(tagId)) {
                selectedTagIds.delete(tagId);
                e.target.classList.remove('selected');
            } else {
                selectedTagIds.add(tagId);
                e.target.classList.add('selected');
            }
            updateHiddenInput();
        }
    });
    
    search.addEventListener('input', () => {
        const val = search.value.toLowerCase();
        Array.from(tagsContainer.children).forEach(tagDiv => {
            const name = tagDiv.textContent.toLowerCase();
            tagDiv.style.display = name.includes(val) ? '' : 'none';
        });
    });
});