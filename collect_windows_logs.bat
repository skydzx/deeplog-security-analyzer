@echo off
REM 应急响应日志收集脚本 - Windows版本
REM 在目标Windows服务器上以管理员身份运行

set TIMESTAMP=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%
set TIMESTAMP=%TIMESTAMP: =%
set OUTPUT_DIR=incident_response_%TIMESTAMP%

mkdir "%OUTPUT_DIR%" 2>nul

echo [+] 开始收集系统日志...

REM 收集系统信息
echo [+] 收集系统信息...
systeminfo > "%OUTPUT_DIR%\system_info.txt" 2>nul

REM 收集网络连接
echo [+] 收集网络连接...
netstat -anob > "%OUTPUT_DIR%\network_connections.txt" 2>nul

REM 收集进程列表
echo [+] 收集进程列表...
tasklist /v > "%OUTPUT_DIR%\process_list.txt" 2>nul

REM 收集计划任务
echo [+] 收集计划任务...
schtasks /query /fo list /v > "%OUTPUT_DIR%\scheduled_tasks.txt" 2>nul

REM 收集用户信息
echo [+] 收集用户信息...
net user > "%OUTPUT_DIR%\users.txt" 2>nul
query user > "%OUTPUT_DIR%\logged_in_users.txt" 2>nul

REM 收集Windows事件日志
echo [+] 收集Windows事件日志...

powershell -Command "& {
    $logs = @('System', 'Application', 'Security')
    foreach ($log in $logs) {
        Get-WinEvent -LogName $log -MaxEvents 5000 -ErrorAction SilentlyContinue |
            ForEach-Object {
                $_.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss.fff') + ' ' + $_.LevelDisplayName + ' EventID=' + $_.Id + ' ' + $_.Message
            } | Out-File -FilePath '%OUTPUT_DIR%\windows_' + $log.ToLower() + '_log.txt' -Encoding UTF8
    }
}" 2>nul

REM 收集IIS日志
echo [+] 收集IIS日志...
for /f "delims=" %%i in ('reg query "HKLM\SYSTEM\CurrentControlSet\Services\W3SVC\Parameters\Virtual Roots" /v * 2^>nul ^| findstr "LOGGING"') do (
    set " IIS_KEY=%%i"
)
if defined IIS_KEY (
    for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Services\W3SVC\Parameters" /v LogFileDir 2^>nul') do (
        set "IIS_LOG_DIR=%%b"
    )
    if defined IIS_LOG_DIR (
        if exist "%IIS_LOG_DIR%\*.log" (
            mkdir "%OUTPUT_DIR%\iis_logs" 2>nul
            copy "%IIS_LOG_DIR%\*.log" "%OUTPUT_DIR%\iis_logs\" >nul 2>nul
        )
    )
)

REM 收集FTP日志
echo [+] 收集FTP日志...
for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Services\MSFTPSVC\Parameters" 2^>nul ^| findstr "Virtual"') do (
    set "FTP_DIR=%%b"
    if exist "%FTP_DIR%\*.log" (
        mkdir "%OUTPUT_DIR%\ftp_logs" 2>nul
        copy "%FTP_DIR%\*.log" "%OUTPUT_DIR%\ftp_logs\" >nul 2>nul
    )
)

REM 收集最近文件访问
echo [+] 收集最近文件访问...
powershell -Command "& {
    Get-Item 'C:\Users\*\AppData\Roaming\Microsoft\Windows\Recent\*' -ErrorAction SilentlyContinue |
        Select-Object Name, CreationTime, LastWriteTime |
        Export-Csv -Path '%OUTPUT_DIR%\recent_files.csv' -NoTypeInformation -Encoding UTF8
}" 2>nul

REM 收集注册表启动项
echo [+] 收集注册表启动项...
reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" > "%OUTPUT_DIR%\registry_run.txt" 2>nul
reg query "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" > "%OUTPUT_DIR%\registry_run_user.txt" 2>nul
reg query "HKLM\SYSTEM\CurrentControlSet\Services" /s /v ImagePath 2>nul | findstr /i "ImagePath" > "%OUTPUT_DIR%\services.txt" 2>nul

REM 收集DNS缓存
echo [+] 收集DNS缓存...
ipconfig /displaydns > "%OUTPUT_DIR%\dns_cache.txt" 2>nul

REM 收集ARP缓存
echo [+] 收集ARP缓存...
arp -a > "%OUTPUT_DIR%\arp_cache.txt" 2>nul

REM 收集路由表
echo [+] 收集路由表...
route print > "%OUTPUT_DIR%\routing_table.txt" 2>nul

REM 收集防火墙状态
echo [+] 收集防火墙状态...
netsh advfirewall show all > "%OUTPUT_DIR%\firewall_status.txt" 2>nul

REM 收集安全策略
echo [+] 收集安全策略...
secedit /export /cfg "%OUTPUT_DIR%\security_policy.inf" >nul 2>nul

REM 压缩收集的数据
echo [+] 压缩收集的数据...
powershell -Command "& {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::CreateFromDirectory('%OUTPUT_DIR%', '%OUTPUT_DIR%.zip')
}" 2>nul

REM 清理临时目录
rmdir /s /q "%OUTPUT_DIR%" 2>nul

echo.
echo ========================================
echo    应急响应日志收集完成
echo ========================================
echo 输出文件: %OUTPUT_DIR%.zip
echo.
echo 使用方法:
echo   1. 解压: unzip %OUTPUT_DIR%.zip
echo   2. 分析: python incident_response.py --auto %OUTPUT_DIR%
echo ========================================

pause
