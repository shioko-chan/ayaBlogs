document.addEventListener('DOMContentLoaded', () => {
    let lastRequest = 0;
    const codeButton = document.getElementById('get-code');
    const timeInterval = 120;
    codeButton.addEventListener('click', () => {
        let emailInput = document.getElementById('email');
        if (!emailInput.checkValidity()) {
            alert('邮箱格式错误');
            return;
        }
        const currentTime = new Date().getTime();
        if (currentTime - lastRequest < timeInterval * 1000) {
            alert("120秒后才能再次发送");
            return;
        }
        lastRequest = currentTime;
        fetch(emailValidateUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: emailInput.value,
            })
        }).then(response => response.json()).then(data => {
            if (data.status == 'success') {
                alert('验证码已发送，请查收');
                let code = document.getElementById("validate-code");
                code.classList.remove("hidden");
            } else if (data.status == 'email-duplicate') {
                let mes = document.getElementById('mes-email');
                mes.classList.remove("hidden");
            } else {
                alert('验证码发送失败，请检查邮箱是否正确');
            }
        })
    }
    );

    const submit = document.getElementById('submit-button');
    submit.addEventListener('click', () => {


        var formData = new FormData(document.getElementById('register-form'));
        if (!formData.get('username')) {
            alert('请输入用户名');
            return;
        }
        if (!formData.get('password')) {
            alert('请输入密码');
            return;
        }
        if (!formData.get('email')) {
            alert('请输入邮箱');
            return;
        }
        if (!formData.get('code')) {
            alert('请输入验证码');
            return;
        }
        let emailInput = document.getElementById('email');
        if (!emailInput.checkValidity()) {
            alert('邮箱格式错误');
            return;
        }
        if (formData.get("repassword") !== formData.get("password")) {
            alert('两次输入密码不一致');
            return;
        }
        if (!formData.get('g-recaptcha-response')) {
            alert('请完成recaptcha验证');
            return;
        }
        fetch(registerUrl, {
            method: 'POST',
            body: formData
        }).then(response => response.json()).then(data => {
            if (data.status == 'success') {
                alert('注册成功');
                window.location.href = loginUrl;
            } else if (data.status == "username-duplicate") {
                let mes = document.getElementById('mes-username');
                mes.classList.remove("hidden");
            } else if (data.status == "email-duplicate") {
                let mes = document.getElementById('mes-email');
                mes.classList.remove("hidden");
            } else if (data.status == "invalid-code") {
                alert("验证码错误");
            }
            else {
                alert('注册失败');
            }
        })
    }
    );
})