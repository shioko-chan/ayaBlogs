function init() {
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

        let gresponse = grecaptcha.getResponse();
        if (!grecaptcha || !gresponse) {
            showPasswordMessages("请完成recaptcha验证");
            return;
        }
        const data = await fetch(gRecaptchaUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                "recaptcha": gresponse
            })
        }).then(response => response.json());
        if (!data.success) {
            switch (data.code) {
                case 1: showPasswordMessages("recaptcha验证未通过"); break;
                case 2: showPasswordMessages("请完成recaptcha验证"); break;
                case 3: showPasswordMessages("recaptcha尝试次数过多，请等待#秒后重试".replace("#", data.data.time)); break;
                case 101: showPasswordMessages("内部错误，可能需要邮件联系开发者，邮箱地址见右下角"); break;
                default: console.log(data); break;
            }
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
                window.location = data.data.space;
            }
            else {
                switch (data.code) {
                    case 1: showPasswordMessages("请输入用户名"); break;
                    case 2: showPasswordMessages("用户名或密码错误"); break;
                    case 101: showPasswordMessages("内部错误，可能需要邮件联系开发者，邮箱地址见右下角"); break;
                    default: console.log(data); break;
                }
            }
        })
    });
}
if (document.readyState !== 'loading') {
    init();
} else {
    document.addEventListener('DOMContentLoaded',
        init,
    )
}
