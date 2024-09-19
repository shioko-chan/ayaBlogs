export function runAfterDOMLoaded(func) {
    if (document.readyState !== 'loading') {
        func();
    } else {
        document.addEventListener('DOMContentLoaded',
            func,
        )
    }
}
