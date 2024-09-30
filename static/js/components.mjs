export function registerDigestList() {
    class DigestList extends HTMLDivElement {
        constructor() {
            super();
        }
        connectedCallback() {
            const template = document.getElementById("digest-list-tmpl");
            const shadowRoot = this.attachShadow({ mode: 'closed' });
            shadowRoot.append(template.content.cloneNode(true));
        }
        disconnectedCallback() {

        }
        static get observedAttributes() {

        }
        attributesChangedCallback(name, oldValue, newValue) {

        }
        adoptedCallback() {

        }
    }
    customElements.define("digest-list", DigestList, { extends: "div" });
}

// { { url_for('page.search', uid = user.id) } }
export function registerSearchBar() {
    class SearchBar extends HTMLDivElement {
        constructor() {
            super();
            this.innerDOM = this.attachShadow({ mode: 'closed' });
            this.innerDOM.append(document.getElementById("search-bar-tmpl").content.cloneNode(true));
            this.rendered = false;
        }
        render() {
            let placeholder = this.getAttribute("placeholder");
            if (placeholder) {
                this.innerDOM.getElementById("search-input").setAttribute("placeholder", placeholder);
            }
            let search_url = this.getAttribute("search_url");
            if (search_url) {
                this.innerDOM.getElementById("search-form").setAttribute("action", search_url);
            }
            this.initSearch(null, null);
        }
        connectedCallback() {
            if (!this.rendered) {
                this.render();
                this.rendered = true;
            }
        }
        disconnectedCallback() {

        }
        static get observedAttributes() {
            return ["placeholder", "search_url"];
        }
        attributesChangedCallback(name, oldValue, newValue) {
            this.render();
        }
        adoptedCallback() {

        }
        initSearch(search_type, search_url) {
            const queryDelay = 500;
            const cacheSize = 200;

            function generateSearchItem(items, label) {
                return items.map(({ content, url }) => `<div class="flex justify-between items-center flex-row border-b-2">
      <a class="search-result text-gray-700 p-1" href="${url}">${content}</a>
      <span class="text-gray-500 text-xs p-1">${label}</span>
    </div>`).join('');
            }

            const searchInput = this.innerDOM.getElementById('search-input');
            const searchResults = this.innerDOM.getElementById('search-results');
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
                    });
                }, queryDelay);
            });
        }
    }
    customElements.define("search-bar", SearchBar, { extends: "div" });
}

export function registerDigestItem() {
    class DigestItem extends HTMLDivElement {
        constructor() {
            super();
            this.innerDOM = this.attachShadow({ mode: 'closed' });
            this.innerDOM.append(document.getElementById("digest-tmpl").content.cloneNode(true));
            this.rendered = false;
            this.attribute_names = ["jump_url", "image_url", "title", "digest", "timestamp", "author", "votes"];
        }
        render() {
            ["title", "digest", "author"].forEach(name => {
                let value = this.getAttribute(name);
                if (value) {
                    this.innerDOM.getElementById(name).innerHTML = value;
                }
            });
            let value = this.getAttribute("image_url");
            if (value) {
                this.innerDOM.getElementById("image").setAttribute("src", value);
            }
            value = this.getAttribute("timestamp");
            if (value) {
                this.innerDOM.getElementById("timestamp").innerHTML = value.toLocalString();
            }
        }
        connectedCallback() {
            if (!this.rendered) {
                this.render();
                this.rendered = true;
            }
        }
        disconnectedCallback() {

        }
        static get observedAttributes() {
            return this.attribute_names;
        }
        attributesChangedCallback(name, oldValue, newValue) {
            this.render();
        }
        adoptedCallback() {

        }
    }
    customElements.define("digest-item", DigestItem, { extends: "div" });
}
