const queryDelay = 200;
const cacheSize = 200;

function generateSearchItem(items, label) {
    return items.map(item => `<div class="flex justify-between items-center flex-row border-b-2">
      <a class="search-result text-gray-700 p-1" href="#">${item}</a>
      <span class="text-gray-500 text-xs p-1">${label}</span>
    </div>
  `).join('');
}

document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('search-input');
    const searchResults = document.getElementById('search-results');
    const cache = new Map();
    const setCache = (key, value) => {
        if (cache.size >= cacheSize) {
            cache.delete(cache.keys().next().value);
        }
        cache.set(key, value);
    };
    searchInput.addEventListener('input', () => {
        if (searchInput.value === '') {
            searchResults.classList.add('hidden');
            return;
        }
        let val = searchInput.value.trim();
        setTimeout(() => {
            let keyword = searchInput.value.trim()
            if (keyword != val) { return }
            console.log(cache)
            if (cache.has(keyword)) {
                let optionHtml = cache.get(keyword);
                if (optionHtml === '') return;
                searchResults.innerHTML = optionHtml;
                searchResults.classList.remove('hidden');
                return;
            }
            fetch(searchUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: keyword
                })
            }).then(response => response.json()).then(data => {
                let optionHtml = generateSearchItem(data.articles, '文章') + generateSearchItem(data.usrs, '用户');
                setCache(keyword, optionHtml);
                if (optionHtml === '') return;
                searchResults.innerHTML = optionHtml;
                searchResults.classList.remove('hidden');
            })
        }, queryDelay);
    });
})