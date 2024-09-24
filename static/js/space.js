import { runAfterDOMLoaded } from './utils.js';
import { marked } from 'https://cdn.jsdelivr.net/npm/marked@14.1.0/+esm';
import DOMPurify from 'https://cdn.jsdelivr.net/npm/dompurify@3.1.6/+esm';

async function solveToast(confirmButton, cancelButton) {
    return new Promise((resolve) => {
        const onConfirm = () => { resolve(true); cleanup(); };
        const onCancel = () => { resolve(false); cleanup(); };
        const cleanup = () => {
            confirmButton.removeEventListener('click', onConfirm);
            cancelButton.removeEventListener('click', onCancel);
        };
        confirmButton.addEventListener('click', onConfirm);
        cancelButton.addEventListener('click', onCancel);
    });
}

function addDeleteListener() {
    const confirmationModal = document.getElementById('confirmation-modal');
    const confirmButton = document.getElementById('confirm-delete-button');
    const cancelButton = document.getElementById('cancel-delete-button');
    document.querySelectorAll('.delete-button').forEach((btn) => {
        btn.addEventListener('click', async () => {
            confirmationModal.classList.remove('hidden');
            if (await solveToast(confirmButton, cancelButton)) {
                const url = btn.getAttribute('data-url');
                fetch(url, {
                    method: "POST", headers: {
                        "Content-Type": "application/json"
                    }
                });
            }
            btn.closest('.passage-container').remove();
            confirmationModal.classList.add('hidden');
        })
    })
}

function convertMD2HTML() {
    document.querySelectorAll('.passage').forEach((element) => {
        element.innerHTML = DOMPurify.sanitize(marked.parse(element.innerHTML));
        if (element.scrollHeight > element.clientHeight) {
            const showMore = document.createElement('div');
            showMore.classList.add('text-sm', 'text-blue-500', 'cursor-pointer', 'mt-2');
            showMore.textContent = '查看更多';
            let showed = false;
            showMore.addEventListener('click', () => {
                if (showed) {
                    element.classList.add('max-h-48');
                    showMore.textContent = '查看更多';
                } else {
                    element.classList.remove('max-h-48');
                    showMore.textContent = '收起';
                }
                showed = !showed;
            });
            element.insertAdjacentElement('afterend', showMore);
        }
    })
}

function moveCaretToEnd(el) {
    const range = document.createRange();
    const sel = window.getSelection();
    range.selectNodeContents(el);
    range.collapse(false);
    sel.removeAllRanges();
    sel.addRange(range);
    el.focus();
}

function addSignEditListener() {
    let inputBox = document.getElementById('sign-input-box');
    let inputButton = document.getElementById('sign-input-button');
    inputButton.addEventListener('click', () => {
        inputBox.contentEditable = true;
        inputBox.focus();
        inputBox.classList.add('bg-gray-500');
    });
    inputBox.addEventListener('input', () => {
        let content = inputBox.innerText;
        if (content.length > 100) {
            inputBox.innerText = content.slice(0, 100);
            moveCaretToEnd(inputBox);
        }
    });
    inputBox.addEventListener('blur', () => {
        inputBox.contentEditable = false;
        inputBox.classList.remove('bg-gray-500');
        fetch(inputButton.getAttribute('data-url'), {
            method: "POST", headers: {
                "Content-Type": "application/json"
            }, body: JSON.stringify({
                sign: inputBox.textContent
            })
        }).then(response => response.json()).then(data => {
            if (data.success) {
                return;
            }
            switch (data.code) {
                case 1: {
                    let toast = document.getElementById("too-frequent");
                    let button = document.getElementById("too-frequent-button");
                    toast.classList.remove("hidden");
                    let buttonSolver = () => {
                        toast.classList.add("hidden");
                        button.removeEventListener("click", buttonSolver);
                    }
                    button.addEventListener("click", buttonSolver);
                    break;
                }
                // solve more status
                default: console.log(data)
            }
        });
    });
}

function addScrollListener() {
    const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                console.log('已滚动到底部');
            }
        });
    });
    const sentinel = document.getElementById('sentinel');
    observer.observe(sentinel);
}

function addVisibilityEditListener() {
    const button = document.getElementById("set-visibility-button");
    const toast = document.getElementById("visibility-modal");
    const confirmButton = document.getElementById('confirm-visibility-change-button');
    const cancelButton = document.getElementById('cancel-visibility-change-button');
    button.addEventListener("click", async () => {
        toast.classList.remove("hidden");
        if (await solveToast(confirmButton, cancelButton)) {
            console.log("confirm");
        }
        toast.classList.add("hidden");
    });
}

export function noneditable() {
    runAfterDOMLoaded(() => {
        convertMD2HTML();
        addScrollListener();
    });
}


export function editable() {
    noneditable();
    runAfterDOMLoaded(() => {
        addDeleteListener();
        addSignEditListener();
        addVisibilityEditListener();
    });
}

