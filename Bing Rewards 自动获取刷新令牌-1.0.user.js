// ==UserScript==
// @name         Bing Rewards 自动获取刷新令牌
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  自动从Microsoft授权页面获取刷新令牌
// @author       輕🌊ꫛꫀˑꪝ(ID28507)
// @icon         https://account.microsoft.com/favicon.ico
// @match        https://login.live.com/oauth20_desktop.srf*
// @match        https://login.live.com/oauth20_authorize.srf*
// @grant        GM_setValue
// @grant        GM_getValue
// @grant        GM_notification
// @grant        GM_setClipboard
// @run-at       document-start
// @homepage       
// @supportURL     
// ==/UserScript==

(function() {
    'use strict';

    // 检查当前页面是否是授权回调页面
    function checkForAuthCode() {
        const url = window.location.href;
        const urlParams = new URLSearchParams(window.location.search);

        // 检查是否在回调页面且包含授权码
        if (url.includes('oauth20_desktop.srf') && urlParams.has('code')) {
            const code = urlParams.get('code');
            console.log('🎯 检测到授权码:', code.substring(0, 20) + '...');

            // 显示处理状态
            showProcessingUI();

            // 获取刷新令牌
            getRefreshTokenFromCode(code);
        }
    }

    // 显示处理界面
    function showProcessingUI() {
        // 创建覆盖层
        const overlay = document.createElement('div');
        overlay.id = 'token-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            z-index: 99999;
            display: flex;
            justify-content: center;
            align-items: center;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        `;

        // 创建内容容器
        const container = document.createElement('div');
        container.style.cssText = `
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            max-width: 600px;
            width: 90%;
            text-align: center;
        `;

        container.innerHTML = `
            <h2 style="color: #0078d4; margin-bottom: 20px;">🔧 Bing Rewards 令牌获取工具</h2>
            <div id="status-content">
                <div style="margin: 20px 0;">
                    <div class="spinner" style="
                        border: 4px solid #f3f3f3;
                        border-top: 4px solid #0078d4;
                        border-radius: 50%;
                        width: 40px;
                        height: 40px;
                        animation: spin 1s linear infinite;
                        margin: 0 auto 15px;
                    "></div>
                    <p style="color: #666; font-size: 16px;">🔄 正在获取刷新令牌...</p>
                </div>
            </div>
        `;

        // 添加旋转动画
        const style = document.createElement('style');
        style.textContent = `
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);

        overlay.appendChild(container);
        document.body.appendChild(overlay);
    }

    // 更新状态显示
    function updateStatus(html) {
        const statusContent = document.getElementById('status-content');
        if (statusContent) {
            statusContent.innerHTML = html;
        }
    }

    // 通过授权码获取刷新令牌
    async function getRefreshTokenFromCode(code) {
        const tokenUrl = "https://login.live.com/oauth20_token.srf";

        const data = new URLSearchParams({
            'client_id': '0000000040170455',
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': 'https://login.live.com/oauth20_desktop.srf',
            'scope': 'service::prod.rewardsplatform.microsoft.com::MBI_SSL'
        });

        try {
            const response = await fetch(tokenUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: data
            });

            if (response.ok) {
                const tokenData = await response.json();

                if (tokenData.refresh_token) {
                    const refreshToken = tokenData.refresh_token;

                    // 保存令牌到本地存储
                    GM_setValue('bing_refresh_token', refreshToken);

                    // 复制到剪贴板
                    GM_setClipboard(refreshToken);

                    // 显示成功信息
                    showSuccessUI(refreshToken);

                    // 发送通知
                    GM_notification({
                        text: '✅ 刷新令牌获取成功！已复制到剪贴板',
                        title: 'Bing Rewards',
                        timeout: 5000
                    });

                    console.log('✅ 刷新令牌获取成功:', refreshToken);
                } else {
                    throw new Error('响应中未找到refresh_token');
                }
            } else {
                throw new Error(`请求失败，状态码: ${response.status}`);
            }
        } catch (error) {
            console.error('❌ 获取令牌失败:', error);
            showErrorUI(error.message);

            GM_notification({
                text: '❌ 获取令牌失败: ' + error.message,
                title: 'Bing Rewards',
                timeout: 5000
            });
        }
    }

    // 显示成功界面
    function showSuccessUI(refreshToken) {
        const maskedToken = refreshToken.substring(0, 20) + '...';

        updateStatus(`
            <div style="text-align: center;">
                <div style="font-size: 48px; color: #28a745; margin-bottom: 15px;">✅</div>
                <h3 style="color: #28a745; margin-bottom: 20px;">刷新令牌获取成功！</h3>

                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #28a745;">
                    <p style="margin: 0; color: #666;">🎯 您的刷新令牌: ${maskedToken}</p>
                </div>

                <div style="text-align: left; background: #e8f4fd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h4 style="color: #0078d4; margin-top: 0;">📋 使用说明:</h4>
                    <ul style="color: #333; margin: 10px 0; padding-left: 20px;">
                        <li>✅ 令牌已自动复制到剪贴板</li>
                        <li>✅ 令牌已保存到浏览器本地存储</li>
                        <li>💡 可以通过控制台 GM_getValue('bing_refresh_token') 获取</li>
                    </ul>
                </div>

                <button onclick="document.getElementById('token-overlay').remove()"
                        style="
                            background: #0078d4;
                            color: white;
                            border: none;
                            padding: 10px 20px;
                            border-radius: 5px;
                            cursor: pointer;
                            font-size: 16px;
                            margin-top: 15px;
                        ">
                    关闭
                </button>
            </div>
        `);
    }

    // 显示错误界面
    function showErrorUI(errorMessage) {
        updateStatus(`
            <div style="text-align: center;">
                <div style="font-size: 48px; color: #dc3545; margin-bottom: 15px;">❌</div>
                <h3 style="color: #dc3545; margin-bottom: 20px;">获取令牌失败</h3>

                <div style="background: #f8d7da; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #dc3545;">
                    <p style="margin: 0; color: #721c24;">错误信息: ${errorMessage}</p>
                </div>

                <div style="text-align: left; background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h4 style="color: #856404; margin-top: 0;">💡 解决建议:</h4>
                    <ul style="color: #333; margin: 10px 0; padding-left: 20px;">
                        <li>检查网络连接是否正常</li>
                        <li>确认已正确完成Microsoft账号授权</li>
                        <li>尝试重新访问授权链接</li>
                    </ul>
                </div>

                <button onclick="document.getElementById('token-overlay').remove()"
                        style="
                            background: #dc3545;
                            color: white;
                            border: none;
                            padding: 10px 20px;
                            border-radius: 5px;
                            cursor: pointer;
                            font-size: 16px;
                            margin-top: 15px;
                        ">
                    关闭
                </button>
            </div>
        `);
    }

    // 在授权页面添加说明
    function addAuthInstructions() {
        if (window.location.href.includes('oauth20_authorize.srf')) {
            // 等待页面加载完成
            setTimeout(() => {
                const body = document.body;
                if (body) {
                    const notice = document.createElement('div');
                    notice.style.cssText = `
                        position: fixed;
                        top: 10px;
                        right: 10px;
                        background: #0078d4;
                        color: white;
                        padding: 15px;
                        border-radius: 8px;
                        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
                        z-index: 10000;
                        font-family: 'Segoe UI', sans-serif;
                        font-size: 14px;
                        max-width: 300px;
                    `;

                    notice.innerHTML = `
                        <div style="font-weight: bold; margin-bottom: 8px;">🔧 Bing Rewards 令牌工具</div>
                        <div>完成授权后，页面会自动跳转并获取刷新令牌</div>
                        <div style="margin-top: 8px; font-size: 12px; opacity: 0.9;">油猴脚本已激活 ✓</div>
                    `;

                    body.appendChild(notice);

                    // 5秒后自动隐藏
                    setTimeout(() => {
                        notice.style.opacity = '0';
                        notice.style.transition = 'opacity 0.5s';
                        setTimeout(() => notice.remove(), 500);
                    }, 5000);
                }
            }, 1000);
        }
    }

    // 添加控制台帮助函数
    window.getBingRefreshToken = function() {
        const token = GM_getValue('bing_refresh_token');
        if (token) {
            console.log('🎯 当前保存的刷新令牌:', token);
            GM_setClipboard(token);
            console.log('✅ 令牌已复制到剪贴板');
            return token;
        } else {
            console.log('❌ 未找到保存的刷新令牌');
            return null;
        }
    };

    // 页面加载时执行
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            checkForAuthCode();
            addAuthInstructions();
        });
    } else {
        checkForAuthCode();
        addAuthInstructions();
    }

    // 监听URL变化（用于单页应用）
    let currentUrl = window.location.href;
    const urlObserver = new MutationObserver(() => {
        if (window.location.href !== currentUrl) {
            currentUrl = window.location.href;
            checkForAuthCode();
            addAuthInstructions();
        }
    });

    urlObserver.observe(document.body, {
        childList: true,
        subtree: true
    });

    console.log('🔧 Bing Rewards 自动获取刷新令牌脚本已加载');
    console.log('💡 使用 getBingRefreshToken() 函数可以获取已保存的令牌');

})();