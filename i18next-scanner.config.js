module.exports = {
    input: [
        'templates/*.html',
        'static/js/*.js'
    ],
    output: './static/locales',
    options: {
        debug: true,
        func: {
            list: ['i18next.t', 'i18n.t'], // 需要提取的翻译函数
            extensions: ['.js'],
        },
        lngs: ['en', 'zh'],
        ns: [
            'translation',
        ],
        defaultLng: 'en',
        defaultNs: 'translation',
        resource: {
            loadPath: 'locales/{{lng}}/{{ns}}.json',
            savePath: 'locales/{{lng}}/{{ns}}.json',
            jsonIndent: 2,
        },
        keySeparator: false,
        nsSeparator: false,
    },
};
