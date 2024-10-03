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
            this.attribute_names = ["jump_url", "image_url", "title", "digest", "timestamp", "author", "votes"];
            this.pending = { "resized": false, "updated": false };
            this.isIntersecting = false;
            const observeCallback = entry => {
                if (!entry.isIntersecting) {
                    this.isIntersecting = false;
                    return;
                }
                if (this.pending.resized) {
                    this.alignByRenderText();
                    this.pending.resized = false;
                }
                if (this.pending.updated) {
                    this.pending.updated = false;
                }
                this.isIntersecting = true;
            };
            const observer = new IntersectionObserver((entries, _) => {
                entries.forEach(observeCallback);
            });
            observer.observe(this);
        }
        maxHeight2px(element, maxHeight) {
            if (maxHeight.includes("px")) {
                return parseInt(maxHeight);
            }
            else if (maxHeight.includes("%")) {
                return parseFloat(maxHeight) * this.getMaxHeight(element.parentElement) / 100.0;
            }
            else switch (maxHeight) {
                case "inherit": return this.getMaxHeight(element.parentElement);
                case "auto":
                case "none": return window.innerHeight;
                default: console.log(maxHeight); return -1;
            }
        }
        getMaxHeight(element) {
            if (!element) {
                return this.maxHeight2px(this, window.getComputedStyle(this).maxHeight);
            }
            return this.maxHeight2px(element, window.getComputedStyle(element).maxHeight);
        }
        textRender(element, text) {
            text = text.replaceAll(/\s+/g, ' ');
            let maxHeight = this.getMaxHeight(element.parentElement);
            element.innerHTML = '';
            for (let i = 1; i <= text.length; i++) {
                if (element.clientHeight > maxHeight) {
                    element.innerHTML = text.slice(0, Math.max(1, i - 4)) + '...';
                    break;
                }
                element.innerHTML = text.slice(0, i);
            }
            element.parentElement.style.height = element.clientHeight + 'px';
            return element.clientHeight;
        }
        alignByRenderText() {
            let ele = null;
            let title = this.getAttribute("title-content") || "暂无标题";
            ele = this.innerDOM.getElementById("title");
            this.textRender(ele, title);
            let digest = this.getAttribute("digest") || "暂无内容";
            ele = this.innerDOM.getElementById("digest");
            let height = this.textRender(ele, digest);
            this.innerDOM.getElementById("image").parentElement.style.height = height + 'px';
        }
        render() {
            this.alignByRenderText();
            ["author"].forEach(name => {
                let value = this.getAttribute(name);
                if (value) {
                    this.innerDOM.getElementById(name).innerHTML = value;
                }
            });
            let value = this.getAttribute("image-url");
            if (value) {
                this.innerDOM.getElementById("image").setAttribute("src", value);
            }
            value = this.getAttribute("timestamp");
            if (value) {
                this.innerDOM.getElementById("timestamp").innerHTML = value.toLocalString();
            }
            let timer = null;
            window.addEventListener("resize", () => {
                if (timer) {
                    clearTimeout(timer);
                }
                timer = setTimeout(() => {
                    if (this.isIntersecting) {
                        this.alignByRenderText();
                        this.pending.resized = false;
                    } else {
                        this.pending.resized = true;
                    }
                }, 500);

            });
        }
        connectedCallback() {
            this.render();
        }
        static get observedAttributes() {
            return this.attribute_names;
        }
        attributesChangedCallback(name, oldValue, newValue) {
            this.pending.updated = true;
        }
        adoptedCallback() {

        }
    }
    customElements.define("digest-item", DigestItem, { extends: "div" });
}
