document.addEventListener('DOMContentLoaded', () => {
    const submit = document.getElementById('submit-button');
    submit.addEventListener('click', () => {
        var formData = new FormData(document.getElementById('login-form'));
        if (!formData.get('username')) {
            alert('请输入用户名');
            return;
        }
        if (!formData.get('password')) {
            alert('请输入密码');
            return;
        }
        if (!formData.get('g-recaptcha-response')) {
            alert('请完成recaptcha验证');
            return;
        }
        fetch(loginUrl, {
            method: 'POST',
            body: formData
        }).then(response => response.json()).then(data => {
            if (data.status == 'success') {
                window.location.href = "/mainpage/" + formData.get('username');
            } else if (data.status == "user-not-exist") {
                alert('用户不存在');
            } else if (data.status == "password-error") {
                alert('用户名或密码错误');
            }
            else {
                alert('注册失败');
            }
        })
    }
    );
})