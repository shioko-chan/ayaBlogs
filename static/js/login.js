document.addEventListener('DOMContentLoaded', () => {
    function showMessages(father, mes, success) {
        for (let span of father.querySelectorAll("div > span")) {
            span.remove();
        }
        const span = document.createElement("span");
        span.innerText = mes;
        span.classList.add((success ? "text-green-500" : "text-red-500"), "text-xs");
        father.appendChild(span);
    }
    const usernameDiv = document.getElementById("username-div");
    const passwordDiv = document.getElementById("password-div");

    function showUsernameMessages(mes, success = false) {
        showMessages(usernameDiv, mes, success);
    }

    function showPasswordMessages(mes, success = false) {
        showMessages(passwordDiv, mes, success);
    }

    const loginForm = document.getElementById("login-form");
    const usernameInput = document.getElementById("username");
    const passwordInput = document.getElementById("password");

    loginForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (!usernameInput.checkValidity()) {
            showUsernameMessages("用户名字符不合法");
            return;
        }

        if (grecaptcha && grecaptcha.getResponse()) {
            const status = await fetch(gRecaptchaUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    "recaptcha": grecaptcha.getResponse()
                })
            }).then(response => response.json()).then(data => data.success);
            if (!status) {
                showPasswordMessages("recaptcha验证未通过");
                return;
            }
        }
        else {
            showPasswordMessages("请完成recaptcha验证");
            return;
        }

        let username = usernameInput.value;
        fetch(loginUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                "password": passwordInput.value,
                "username": username,
            })
        }).then(response => response.json()).then(data => {
            if (data.success) {
                window.location = data.data.mainpage;
            }
            else {
                showPasswordMessages(data.message);
            }
        })
    });
})