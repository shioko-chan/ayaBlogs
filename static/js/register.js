document.addEventListener("DOMContentLoaded", () => {
    function showMessages(father, mes, success) {

        for (let span of father.querySelectorAll("div > span")) {
            span.remove();
        }
        const span = document.createElement("span");
        span.innerText = mes;
        span.classList.add((success ? "text-green-500" : "text-red-500"), "text-xs");
        father.appendChild(span);
    }

    const emailDiv = document.getElementById("email-div");
    const codeDiv = document.getElementById("code-div");
    const usernameDiv = document.getElementById("username-div");
    const passwordDiv = document.getElementById("password-div");
    const retypePasswordDiv = document.getElementById("retype-password-div");
    function showEmailMessages(mes, success = false) {
        showMessages(emailDiv, mes, success);
    }

    function showCodeMessages(mes, success = false) {
        showMessages(codeDiv, mes, success);
    }

    function showUsernameMessages(mes, success = false) {
        showMessages(usernameDiv, mes, success);
    }

    function showPasswordMessages(mes, success = false) {
        showMessages(passwordDiv, mes, success);
    }

    function showRetypePasswordMessages(mes, success = false) {
        showMessages(retypePasswordDiv, mes, success);
    }

    function setCountDown(cnt) {
        const timer = setInterval(() => {
            if (cnt <= 0) {
                codeButton.innerText = "获取验证码";
                codeButton.classList.remove("bg-blue-300");
                codeButton.classList.remove("cursor-not-allowed");
                codeButton.classList.add("bg-blue-500");
                clearInterval(timer);
                return;
            }
            codeButton.classList.add("bg-blue-300");
            codeButton.classList.add("cursor-not-allowed");
            codeButton.classList.remove("bg-blue-500");
            codeButton.innerText = `${cnt} 秒`;
            cnt -= 1;
        }, 1000);
    }

    let latestReqTime = 0;
    let latestEmail = "";
    let isReceived = false;
    let hasError = false;
    const codeButton = document.getElementById("code-get-button");
    const codeInput = document.getElementById("code");
    const emailInput = document.getElementById("email");

    codeButton.addEventListener("click", async () => {
        codeButton.disabled = true;
        await (async () => {
            if (!emailInput.checkValidity()) {
                showEmailMessages("邮箱格式错误");
                return;
            }

            if (hasError && latestEmail === emailInput.value) {
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
                    showEmailMessages("recaptcha验证未通过");
                    return;
                }
            }
            else {
                showEmailMessages("请完成recaptcha验证");
                return;
            }

            const currentTime = new Date().getTime();
            if (currentTime - latestReqTime < mailSendInterval * 1000) {
                return;
            }

            latestEmail = emailInput.value;
            fetch(emailValidateUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    "email": latestEmail,
                })
            }).then(response => response.json()).then(data => {
                if (data.success) {
                    codeInput.focus();
                    showEmailMessages("验证码已发送, 请查收", true);
                    latestReqTime = new Date().getTime();
                    isReceived = true;
                    setCountDown(mailSendInterval);
                } else {
                    switch (data.code) {
                        case 1:
                            latestReqTime = Math.round(data.data.timestamp * 1000);
                            setCountDown(mailSendInterval - Math.round((new Date().getTime() - latestReqTime) / 1000));
                            break;
                        case 2:
                            showEmailMessages("邮箱地址不可用");
                            hasError = true;
                            break;
                        case 3:
                            showEmailMessages("邮箱地址已被注册");
                            hasError = true;
                            break;
                        default:
                            console.log(data);
                    }
                }
            });
        })();
        codeButton.disabled = false;
    });

    const emailForm = document.getElementById("email-form");
    const registerForm = document.getElementById("register-form");

    emailForm.addEventListener("submit", (event) => {
        event.preventDefault();
        if (!emailInput.checkValidity()) {
            showEmailMessages("邮箱格式错误");
            return;
        }
        if (!codeInput.checkValidity()) {
            showCodeMessages("验证码格式错误");
            return;
        }
        if (!isReceived) {
            showEmailMessages("请先获取验证码");
            return;
        }
        if (latestEmail !== emailInput.value) {
            showEmailMessages("请重新获取验证码");
            return;
        }
        fetch(emailValidateUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                "validate_code": codeInput.value
            })
        }).then(response => response.json()).then(data => {
            if (data.success) {
                registerForm.classList.remove("hidden");
                emailForm.classList.add("hidden");
            } else {
                switch (data.code) {
                    case 11:
                        showCodeMessages(data.message);
                        break;
                    case 12:
                        showCodeMessages(data.message);
                        break;
                    case 13:
                        showEmailMessages(data.message);
                        break;
                    default:
                        console.log(data);
                }
            }
        })
    });

    const usernameInput = document.getElementById("username");
    const passwordInput = document.getElementById("password");
    const retypePasswordInput = document.getElementById("retype-password");

    registerForm.addEventListener("submit", (event) => {
        event.preventDefault();
        if (!usernameInput.checkValidity()) {
            showUsernameMessages("用户名字符不合法");
            return;
        }
        if (passwordInput.value.length < 6) {
            showPasswordMessages("建议使用6位以上混合字母、数字、符号的强密码");
            return;
        }
        if (passwordInput.value !== retypePasswordInput.value) {
            showRetypePasswordMessages("两次输入密码不一致");
            return;
        }
        fetch(registerUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                "password": passwordInput.value,
                "username": usernameInput.value,
            }),
            redirect: "follow"
        }).then(response => response.json()).then(data => {
            if (data.success) {
                window.location = loginUrl;
            } else {
                switch (data.code) {
                    case 1:
                        registerForm.classList.add("hidden");
                        emailForm.classList.remove("hidden");
                        showEmailMessages("尚未验证邮箱");
                        break;
                    case 2:
                        showUsernameMessages(data.message);
                        break;
                    case 3:
                        showUsernameMessages("用户名已被占用");
                        break;
                    case 4:
                        showPasswordMessages(data.message);
                        break;
                    case 5:
                        registerForm.classList.add("hidden");
                        emailForm.classList.remove("hidden");
                        showEmailMessages(data.message);
                        break;
                    default:
                        console.log(data);
                }
            }
        })
    });
})