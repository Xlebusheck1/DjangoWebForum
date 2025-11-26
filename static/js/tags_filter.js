document.addEventListener('DOMContentLoaded', function() {
  var search = document.getElementById('ask-tagsearch');
  if (search) {
    search.addEventListener('input', function() {
      let val = this.value.toLowerCase();
      let tags = document.querySelectorAll('#ask-tagchoices .ask-tag');
      tags.forEach(function(label) {
        let name = label.textContent.toLowerCase();
        label.style.display = name.includes(val) ? '' : 'none';
      });
    });
  }
});
