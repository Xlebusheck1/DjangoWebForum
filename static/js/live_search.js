document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("header-search-input");
  const container = document.getElementById("questions-container");
  
  if (!input || !container) {
    console.log("Live search: Elements not found on this page");
    return;
  }

  let timer = null;
  let isSearching = false;


  const originalContent = container.innerHTML;
  const originalQuestions = Array.from(container.querySelectorAll(".question"));

  
  function displayResults(questionIds) {
    if (questionIds.length === 0) {
      
      container.innerHTML = '<p class="no-results">Вопросы не найдены</p>';
      return;
    }

   
    const questionMap = {};
    originalQuestions.forEach(question => {
      const id = question.dataset.questionId;
      if (id) {
        questionMap[id] = question.outerHTML;
      }
    });

    
    let newHTML = '';
    questionIds.forEach(id => {
      if (questionMap[id]) {
        newHTML += questionMap[id];
      }
    });

   
    const remainingIds = Object.keys(questionMap).filter(id => !questionIds.includes(id));
    remainingIds.forEach(id => {
      if (questionMap[id]) {
        newHTML += questionMap[id];
      }
    });

    container.innerHTML = newHTML;
  }

  
  function performSearch(searchTerm) {
    if (isSearching || !searchTerm.trim()) return;
    
    isSearching = true;
    
    fetch(`/api/search-order/?q=${encodeURIComponent(searchTerm)}`)
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        const order = data.order || [];
        console.log("Search results:", order.length, "questions found");
        
        if (order.length === 0) {
         
          container.innerHTML = '<p class="no-results">По запросу "' + searchTerm + '" ничего не найдено</p>';
        } else {
          displayResults(order.map(id => String(id)));
        }
      })
      .catch(error => {
        console.error('Search error:', error);
        container.innerHTML = '<p class="error">Ошибка при поиске</p>';
      })
      .finally(() => {
        isSearching = false;
      });
  }

 
  input.addEventListener("input", () => {
    const searchTerm = input.value.trim();
    clearTimeout(timer);

    if (searchTerm === '') {    
      container.innerHTML = originalContent;
      return;
    }    
    timer = setTimeout(() => {
      performSearch(searchTerm);
    }, 300);
  });
  console.log("Live search initialized");
});