import { runAfterDOMLoaded } from './utils.js';
import DOMPurify from 'https://cdn.jsdelivr.net/npm/dompurify@3.1.6/+esm';

export function search(search_type, search_url) {
    runAfterDOMLoaded(() => {
        const queryDelay = 500;
        const cacheSize = 200;

        function generateSearchItem(items, label) {
            return items.map(({ text, url }) => `<div class="flex justify-between items-center flex-row border-b-2">
      <a class="search-result text-gray-700 p-1" href="${url}">${text}</a>
      <span class="text-gray-500 text-xs p-1">${label}</span>
    </div>`).join('');
        }

        const searchInput = document.getElementById('search-input');
        const searchResults = document.getElementById('search-results');
        const cache = new Map();

        function setCache(key, value) {
            if (cache.size >= cacheSize) {
                cache.delete(cache.keys().next().value);
            }
            cache.set(key, value);
        };

        let timer;
        searchInput.addEventListener('input', () => {
            if (searchInput.value === '') {
                searchResults.classList.add('hidden');
                return;
            }
            let val = searchInput.value.trim();
            clearTimeout(timer);
            timer = setTimeout(() => {
                let keyword = searchInput.value.trim();
                if (keyword !== val) { return }
                console.log(keyword);
                if (cache.has(keyword)) {
                    let optionHtml = cache.get(keyword);
                    if (optionHtml === '') return;
                    searchResults.innerHTML = optionHtml;
                    searchResults.classList.remove('hidden');
                    return;
                }
                fetch(search_url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        type: search_type,
                        query: keyword,
                    })
                }).then(response => response.json()).then(resp => {
                    if (!resp.success) {
                        return;
                    }
                    let data = resp.data;
                    console.log(data)
                    let optionHtml = '';
                    switch (search_type) {
                        case "all": optionHtml = generateSearchItem(data.passages, '文章') + generateSearchItem(data.usrs, '用户'); break;
                        case "user": optionHtml = generateSearchItem(data.usrs, '用户'); break;
                        case "passage": optionHtml = generateSearchItem(data.passages, '文章'); break;
                        default: console.log("wrong search type");
                    }
                    optionHtml = DOMPurify.sanitize(optionHtml);
                    setCache(keyword, optionHtml);
                    if (optionHtml === '') return;
                    searchResults.innerHTML = optionHtml;
                    searchResults.classList.remove('hidden');
                })
            }, queryDelay);
        });
    });
}
