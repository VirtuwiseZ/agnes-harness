using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Reflection;
using System.Windows.Forms;
using Microsoft.Win32;

namespace AIPhysicsAgent.Installer
{
    public class UninstallForm : Form
    {
        private Label lblTitle;
        private Label lblDesc;
        private CheckBox chkKeepWorkspace;
        private Button btnUninstall;
        private Button btnCancel;
        private ProgressBar progressBar;
        private Label lblStatus;
        private string installDir;

        public UninstallForm()
        {
            InitializeComponent();
            installDir = AppDomain.CurrentDomain.BaseDirectory.TrimEnd('\\', '/');
        }

        private void InitializeComponent()
        {
            this.Text = "AI 物理科研工作站 - 卸载程序";
            this.Size = new Size(520, 310);
            this.StartPosition = FormStartPosition.CenterScreen;
            this.FormBorderStyle = FormBorderStyle.FixedDialog;
            this.MaximizeBox = false;
            this.MinimizeBox = false;
            this.BackColor = Color.FromArgb(248, 249, 252);
            this.Font = new Font("Microsoft YaHei", 9F, FontStyle.Regular, GraphicsUnit.Point);

            try
            {
                string iconPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "app.ico");
                if (File.Exists(iconPath))
                {
                    this.Icon = new Icon(iconPath);
                }
            }
            catch { }

            // Header Panel
            Panel pnlHeader = new Panel();
            pnlHeader.Dock = DockStyle.Top;
            pnlHeader.Height = 70;
            pnlHeader.BackColor = Color.FromArgb(18, 30, 66);

            lblTitle = new Label();
            lblTitle.Text = "卸载 AI 物理科研工作站";
            lblTitle.Font = new Font("Microsoft YaHei", 12F, FontStyle.Bold);
            lblTitle.ForeColor = Color.White;
            lblTitle.Location = new Point(24, 14);
            lblTitle.AutoSize = true;
            pnlHeader.Controls.Add(lblTitle);

            Label lblSub = new Label();
            lblSub.Text = "即将从您的计算机上移除该软件及相关快捷方式与注册信息";
            lblSub.Font = new Font("Microsoft YaHei", 8.5F);
            lblSub.ForeColor = Color.FromArgb(180, 205, 255);
            lblSub.Location = new Point(25, 40);
            lblSub.AutoSize = true;
            pnlHeader.Controls.Add(lblSub);

            this.Controls.Add(pnlHeader);

            // Body Description
            lblDesc = new Label();
            lblDesc.Text = "确定要从当前计算机中完全卸载 AI 物理科研工作站及其所有组件吗？";
            lblDesc.Location = new Point(24, 88);
            lblDesc.Size = new Size(460, 40);
            this.Controls.Add(lblDesc);

            // Keep Workspace Checkbox
            chkKeepWorkspace = new CheckBox();
            chkKeepWorkspace.Text = "保留工作区中用户自建的物理研究成果与历史报告 (agh-workspace/)";
            chkKeepWorkspace.Checked = true;
            chkKeepWorkspace.Location = new Point(27, 130);
            chkKeepWorkspace.AutoSize = true;
            chkKeepWorkspace.ForeColor = Color.FromArgb(30, 41, 59);
            this.Controls.Add(chkKeepWorkspace);

            // Progress Bar
            progressBar = new ProgressBar();
            progressBar.Location = new Point(27, 165);
            progressBar.Size = new Size(450, 16);
            progressBar.Visible = false;
            this.Controls.Add(progressBar);

            // Status Label
            lblStatus = new Label();
            lblStatus.Location = new Point(27, 186);
            lblStatus.Size = new Size(450, 20);
            lblStatus.ForeColor = Color.FromArgb(100, 116, 139);
            lblStatus.Text = "";
            this.Controls.Add(lblStatus);

            // Buttons
            btnUninstall = new Button();
            btnUninstall.Text = "确认卸载";
            btnUninstall.Size = new Size(100, 32);
            btnUninstall.Location = new Point(265, 220);
            btnUninstall.BackColor = Color.FromArgb(225, 29, 72);
            btnUninstall.ForeColor = Color.White;
            btnUninstall.FlatStyle = FlatStyle.Flat;
            btnUninstall.FlatAppearance.BorderSize = 0;
            btnUninstall.Cursor = Cursors.Hand;
            btnUninstall.Click += BtnUninstall_Click;
            this.Controls.Add(btnUninstall);

            btnCancel = new Button();
            btnCancel.Text = "取消";
            btnCancel.Size = new Size(100, 32);
            btnCancel.Location = new Point(377, 220);
            btnCancel.BackColor = Color.FromArgb(226, 232, 240);
            btnCancel.ForeColor = Color.FromArgb(30, 41, 59);
            btnCancel.FlatStyle = FlatStyle.Flat;
            btnCancel.FlatAppearance.BorderSize = 0;
            btnCancel.Cursor = Cursors.Hand;
            btnCancel.Click += (s, e) => this.Close();
            this.Controls.Add(btnCancel);
        }

        private void BtnUninstall_Click(object sender, EventArgs e)
        {
            btnUninstall.Enabled = false;
            btnCancel.Enabled = false;
            progressBar.Visible = true;
            progressBar.Value = 10;
            lblStatus.Text = "正在停止后台守护进程...";
            Application.DoEvents();

            try
            {
                // 1. 尝试终止可能正在运行的后台服务
                try
                {
                    ProcessStartInfo psiStop = new ProcessStartInfo();
                    psiStop.FileName = "node.exe";
                    psiStop.Arguments = "\"" + Path.Combine(installDir, "packages\\cli\\dist\\local\\agnes.mjs") + "\" daemon stop";
                    psiStop.CreateNoWindow = true;
                    psiStop.UseShellExecute = false;
                    using (Process p = Process.Start(psiStop))
                    {
                        if (p != null) p.WaitForExit(3000);
                    }
                }
                catch { }

                progressBar.Value = 35;
                lblStatus.Text = "正在清理桌面及开始菜单快捷方式...";
                Application.DoEvents();

                // 2. 清理桌面快捷方式
                string desktop = Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory);
                string desktopLnk = Path.Combine(desktop, "AI 物理科研工作站.lnk");
                if (File.Exists(desktopLnk)) { try { File.Delete(desktopLnk); } catch { } }

                // 3. 清理开始菜单程序组
                string startMenu = Environment.GetFolderPath(Environment.SpecialFolder.Programs);
                string appGroup = Path.Combine(startMenu, "AI 物理科研工作站");
                if (Directory.Exists(appGroup))
                {
                    try { Directory.Delete(appGroup, true); } catch { }
                }

                progressBar.Value = 60;
                lblStatus.Text = "正在注销 Windows 系统已安装应用注册表项...";
                Application.DoEvents();

                // 4. 清理 Windows 注册表 Uninstall 项
                try
                {
                    using (RegistryKey key = Registry.CurrentUser.OpenSubKey(@"Software\Microsoft\Windows\CurrentVersion\Uninstall", true))
                    {
                        if (key != null)
                        {
                            key.DeleteSubKeyTree("AIPhysicsAgent", false);
                        }
                    }
                }
                catch { }

                progressBar.Value = 85;
                lblStatus.Text = "正在清理程序文件...";
                Application.DoEvents();

                // 5. 准备延迟清理主目录
                string workspacePath = Path.Combine(installDir, "agh-workspace");
                bool keepWorkspace = chkKeepWorkspace.Checked && Directory.Exists(workspacePath);

                string cmdArgs;
                if (keepWorkspace)
                {
                    // 仅删除核心程序目录与脚本，保留 agh-workspace
                    cmdArgs = string.Format("/c ping 127.0.0.1 -n 2 > nul & for /d %i in (\"{0}\\*\") do @if /i not \"%~nxi\"==\"agh-workspace\" rmdir /s /q \"%i\" & for %f in (\"{0}\\*\") do @del /f /q \"%f\"", installDir);
                }
                else
                {
                    // 完全清空目录
                    cmdArgs = string.Format("/c ping 127.0.0.1 -n 2 > nul & rmdir /s /q \"{0}\"", installDir);
                }

                progressBar.Value = 100;
                lblStatus.Text = "卸载完成！";
                Application.DoEvents();

                MessageBox.Show(this, "AI 物理科研工作站已成功从您的计算机中完成卸载。", "卸载成功", MessageBoxButtons.OK, MessageBoxIcon.Information);

                // 启动延迟删除脚本并退出自身
                ProcessStartInfo psiDel = new ProcessStartInfo("cmd.exe", cmdArgs);
                psiDel.CreateNoWindow = true;
                psiDel.UseShellExecute = false;
                Process.Start(psiDel);

                this.Close();
            }
            catch (Exception ex)
            {
                MessageBox.Show(this, "卸载过程中遇到异常: " + ex.Message, "提示", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                this.Close();
            }
        }

        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new UninstallForm());
        }
    }
}
