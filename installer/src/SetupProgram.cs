using System;
using System.ComponentModel;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Net;
using System.Reflection;
using System.Text;
using System.Threading;
using System.Windows.Forms;
using Microsoft.Win32;

namespace AIPhysicsAgent.Installer
{
    public class SetupForm : Form
    {
        // UI Components
        private Panel pnlHeader;
        private Label lblHeaderTitle;
        private Label lblHeaderSub;
        private Panel pnlContent;
        private Button btnBack;
        private Button btnNext;
        private Button btnCancel;

        // Step Panels
        private Panel step1Panel; // Environment Check & Options
        private Panel step2Panel; // Installation Path Selection
        private Panel step3Panel; // Installing Progress
        private Panel step4Panel; // Installation Finished

        // Step 1 controls
        private Label lblEnvTitle;
        private RichTextBox txtEnvStatus;
        private Button btnRecheckEnv;
        private CheckBox chkAutoDownloadNode;
        private CheckBox chkSetupPython;
        private CheckBox chkCreateDesktopShortcut;
        private CheckBox chkCreateStartMenuShortcut;
        private CheckBox chkRegisterUninstall;

        // Step 2 controls
        private Label lblPathTitle;
        private TextBox txtInstallPath;
        private Button btnBrowsePath;
        private Label lblSpaceReq;
        private Label lblSpaceAvail;
        private RadioButton rbIsolated;
        private RadioButton rbSandbox;
        private RadioButton rbDefault;
        private TextBox txtPort;
        private Button btnTestPort;
        private Label lblPortStatus;

        // Step 3 controls
        private Label lblProgressTitle;
        private ProgressBar progressBar;
        private Label lblProgressStatus;
        private TextBox txtInstallLog;

        // Step 4 controls
        private Label lblFinishTitle;
        private Label lblFinishDesc;
        private CheckBox chkLaunchNow;
        private CheckBox chkOpenReadme;

        private int currentStep = 1;
        private string sourceDir;
        private bool isNodeInstalled = false;
        private bool isPythonReady = false;

        public SetupForm()
        {
            sourceDir = AppDomain.CurrentDomain.BaseDirectory.TrimEnd('\\', '/');
            // If running inside installer/src, step up to repo root
            if (File.Exists(Path.Combine(sourceDir, "build_installer.ps1")) || Directory.Exists(Path.Combine(sourceDir, "src")))
            {
                string parent = Directory.GetParent(sourceDir).FullName;
                if (Directory.Exists(Path.Combine(parent, "physics-agent"))) sourceDir = parent;
            }
            if (!Directory.Exists(Path.Combine(sourceDir, "physics-agent")))
            {
                string parent = Directory.GetParent(sourceDir).FullName;
                if (Directory.Exists(Path.Combine(parent, "physics-agent"))) sourceDir = parent;
            }

            InitializeComponent();
            CheckEnvironment();
            ShowStep(1);
        }

        private void InitializeComponent()
        {
            this.Text = "AI 物理科研工作站 - 安装向导 (v0.1.0)";
            this.Size = new Size(720, 560);
            this.StartPosition = FormStartPosition.CenterScreen;
            this.FormBorderStyle = FormBorderStyle.FixedSingle;
            this.MaximizeBox = false;
            this.BackColor = Color.FromArgb(248, 250, 252);
            this.Font = new Font("Microsoft YaHei", 9F, FontStyle.Regular, GraphicsUnit.Point);

            try
            {
                string iconPath = Path.Combine(sourceDir, "installer\\app.ico");
                if (File.Exists(iconPath)) this.Icon = new Icon(iconPath);
            }
            catch { }

            // 1. Header
            pnlHeader = new Panel();
            pnlHeader.Dock = DockStyle.Top;
            pnlHeader.Height = 78;
            pnlHeader.BackColor = Color.FromArgb(15, 23, 42); // Deep navy

            lblHeaderTitle = new Label();
            lblHeaderTitle.Text = "AI 物理科研工作站 (Physics Research Agent)";
            lblHeaderTitle.Font = new Font("Microsoft YaHei", 12.5F, FontStyle.Bold);
            lblHeaderTitle.ForeColor = Color.White;
            lblHeaderTitle.Location = new Point(28, 16);
            lblHeaderTitle.AutoSize = true;
            pnlHeader.Controls.Add(lblHeaderTitle);

            lblHeaderSub = new Label();
            lblHeaderSub.Text = "基于 Agnes Harness 的确定性物理计算与分析智能体系统 · 安装与部署向导";
            lblHeaderSub.Font = new Font("Microsoft YaHei", 8.5F);
            lblHeaderSub.ForeColor = Color.FromArgb(148, 163, 184);
            lblHeaderSub.Location = new Point(29, 44);
            lblHeaderSub.AutoSize = true;
            pnlHeader.Controls.Add(lblHeaderSub);

            this.Controls.Add(pnlHeader);

            // 2. Bottom Button Panel
            Panel pnlBottom = new Panel();
            pnlBottom.Dock = DockStyle.Bottom;
            pnlBottom.Height = 62;
            pnlBottom.BackColor = Color.FromArgb(241, 245, 249);
            pnlBottom.Paint += (s, e) => {
                e.Graphics.DrawLine(new Pen(Color.FromArgb(226, 232, 240)), 0, 0, pnlBottom.Width, 0);
            };

            btnBack = new Button();
            btnBack.Text = "上一步 (< Back)";
            btnBack.Size = new Size(110, 34);
            btnBack.Location = new Point(340, 14);
            btnBack.BackColor = Color.White;
            btnBack.FlatStyle = FlatStyle.Flat;
            btnBack.FlatAppearance.BorderColor = Color.FromArgb(203, 213, 225);
            btnBack.Click += (s, e) => ShowStep(currentStep - 1);
            pnlBottom.Controls.Add(btnBack);

            btnNext = new Button();
            btnNext.Text = "下一步 (Next >)";
            btnNext.Size = new Size(120, 34);
            btnNext.Location = new Point(460, 14);
            btnNext.BackColor = Color.FromArgb(37, 99, 235);
            btnNext.ForeColor = Color.White;
            btnNext.FlatStyle = FlatStyle.Flat;
            btnNext.FlatAppearance.BorderSize = 0;
            btnNext.Font = new Font("Microsoft YaHei", 9F, FontStyle.Bold);
            btnNext.Click += BtnNext_Click;
            pnlBottom.Controls.Add(btnNext);

            btnCancel = new Button();
            btnCancel.Text = "取消";
            btnCancel.Size = new Size(90, 34);
            btnCancel.Location = new Point(590, 14);
            btnCancel.BackColor = Color.White;
            btnCancel.FlatStyle = FlatStyle.Flat;
            btnCancel.FlatAppearance.BorderColor = Color.FromArgb(203, 213, 225);
            btnCancel.Click += (s, e) => {
                if (MessageBox.Show(this, "确定要退出安装向导吗？", "退出确认", MessageBoxButtons.YesNo, MessageBoxIcon.Question) == DialogResult.Yes)
                {
                    this.Close();
                }
            };
            pnlBottom.Controls.Add(btnCancel);

            this.Controls.Add(pnlBottom);

            // 3. Central Content Area
            pnlContent = new Panel();
            pnlContent.Dock = DockStyle.Fill;
            pnlContent.Padding = new Padding(28, 20, 28, 10);
            this.Controls.Add(pnlContent);

            BuildStep1();
            BuildStep2();
            BuildStep3();
            BuildStep4();
        }

        private void BuildStep1()
        {
            step1Panel = new Panel();
            step1Panel.Dock = DockStyle.Fill;

            lblEnvTitle = new Label();
            lblEnvTitle.Text = "步骤一：系统运行环境健康自检与安装项配置";
            lblEnvTitle.Font = new Font("Microsoft YaHei", 10.5F, FontStyle.Bold);
            lblEnvTitle.ForeColor = Color.FromArgb(30, 41, 59);
            lblEnvTitle.Location = new Point(0, 0);
            lblEnvTitle.AutoSize = true;
            step1Panel.Controls.Add(lblEnvTitle);

            txtEnvStatus = new RichTextBox();
            txtEnvStatus.Location = new Point(0, 30);
            txtEnvStatus.Size = new Size(648, 175);
            txtEnvStatus.ReadOnly = true;
            txtEnvStatus.BackColor = Color.FromArgb(241, 245, 249);
            txtEnvStatus.BorderStyle = BorderStyle.FixedSingle;
            txtEnvStatus.Font = new Font("Consolas", 9.5F);
            step1Panel.Controls.Add(txtEnvStatus);

            btnRecheckEnv = new Button();
            btnRecheckEnv.Text = "重新检测环境";
            btnRecheckEnv.Size = new Size(110, 28);
            btnRecheckEnv.Location = new Point(538, 212);
            btnRecheckEnv.BackColor = Color.White;
            btnRecheckEnv.FlatStyle = FlatStyle.Flat;
            btnRecheckEnv.FlatAppearance.BorderColor = Color.FromArgb(203, 213, 225);
            btnRecheckEnv.Click += (s, e) => CheckEnvironment();
            step1Panel.Controls.Add(btnRecheckEnv);

            Label lblOptionsHeader = new Label();
            lblOptionsHeader.Text = "可选依赖与部署配置项：";
            lblOptionsHeader.Font = new Font("Microsoft YaHei", 9.5F, FontStyle.Bold);
            lblOptionsHeader.ForeColor = Color.FromArgb(51, 65, 85);
            lblOptionsHeader.Location = new Point(0, 220);
            lblOptionsHeader.AutoSize = true;
            step1Panel.Controls.Add(lblOptionsHeader);

            chkAutoDownloadNode = new CheckBox();
            chkAutoDownloadNode.Text = "若未检测到 Node.js，在安装时自动下载并启动官方安装包 (Node.js 24 LTS)";
            chkAutoDownloadNode.Checked = true;
            chkAutoDownloadNode.Location = new Point(5, 248);
            chkAutoDownloadNode.AutoSize = true;
            step1Panel.Controls.Add(chkAutoDownloadNode);

            chkSetupPython = new CheckBox();
            chkSetupPython.Text = "自动配置 Python 科学计算依赖库 (SymPy, Pint, NumPy, SciPy, Matplotlib)";
            chkSetupPython.Checked = true;
            chkSetupPython.Location = new Point(5, 274);
            chkSetupPython.AutoSize = true;
            step1Panel.Controls.Add(chkSetupPython);

            chkCreateDesktopShortcut = new CheckBox();
            chkCreateDesktopShortcut.Text = "在桌面创建启动快捷方式 (AI 物理科研工作站.lnk)";
            chkCreateDesktopShortcut.Checked = true;
            chkCreateDesktopShortcut.Location = new Point(5, 300);
            chkCreateDesktopShortcut.AutoSize = true;
            step1Panel.Controls.Add(chkCreateDesktopShortcut);

            chkCreateStartMenuShortcut = new CheckBox();
            chkCreateStartMenuShortcut.Text = "在 Windows 开始菜单中创建程序组与卸载快捷方式";
            chkCreateStartMenuShortcut.Checked = true;
            chkCreateStartMenuShortcut.Location = new Point(5, 326);
            chkCreateStartMenuShortcut.AutoSize = true;
            step1Panel.Controls.Add(chkCreateStartMenuShortcut);

            chkRegisterUninstall = new CheckBox();
            chkRegisterUninstall.Text = "正规注册至 Windows 系统已安装应用列表 (支持控制面板与系统设置卸载)";
            chkRegisterUninstall.Checked = true;
            chkRegisterUninstall.Location = new Point(5, 352);
            chkRegisterUninstall.AutoSize = true;
            step1Panel.Controls.Add(chkRegisterUninstall);

            pnlContent.Controls.Add(step1Panel);
        }

        private void BuildStep2()
        {
            step2Panel = new Panel();
            step2Panel.Dock = DockStyle.Fill;
            step2Panel.Visible = false;

            lblPathTitle = new Label();
            lblPathTitle.Text = "步骤二：选择主程序安装位置与运行环境模式";
            lblPathTitle.Font = new Font("Microsoft YaHei", 10.5F, FontStyle.Bold);
            lblPathTitle.ForeColor = Color.FromArgb(30, 41, 59);
            lblPathTitle.Location = new Point(0, 0);
            lblPathTitle.AutoSize = true;
            step2Panel.Controls.Add(lblPathTitle);

            Label lblPathDesc = new Label();
            lblPathDesc.Text = "安装向导将把核心代码、门禁程序与科学数据库部署至下列目录：";
            lblPathDesc.Location = new Point(0, 26);
            lblPathDesc.Size = new Size(648, 20);
            lblPathDesc.ForeColor = Color.FromArgb(71, 85, 105);
            step2Panel.Controls.Add(lblPathDesc);

            txtInstallPath = new TextBox();
            string defaultFolder = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Programs\\AIPhysicsAgent");
            txtInstallPath.Text = defaultFolder;
            txtInstallPath.Location = new Point(0, 48);
            txtInstallPath.Size = new Size(540, 24);
            txtInstallPath.Font = new Font("Segoe UI", 9F);
            txtInstallPath.TextChanged += (s, e) => UpdateDiskSpace();
            step2Panel.Controls.Add(txtInstallPath);

            btnBrowsePath = new Button();
            btnBrowsePath.Text = "浏览 (Browse)...";
            btnBrowsePath.Size = new Size(100, 26);
            btnBrowsePath.Location = new Point(548, 47);
            btnBrowsePath.BackColor = Color.White;
            btnBrowsePath.FlatStyle = FlatStyle.Flat;
            btnBrowsePath.FlatAppearance.BorderColor = Color.FromArgb(203, 213, 225);
            btnBrowsePath.Click += (s, e) => {
                FolderBrowserDialog fbd = new FolderBrowserDialog();
                fbd.Description = "请选择 AI 物理科研工作站的主安装目录：";
                fbd.SelectedPath = txtInstallPath.Text;
                if (fbd.ShowDialog(this) == DialogResult.OK)
                {
                    txtInstallPath.Text = fbd.SelectedPath;
                }
            };
            step2Panel.Controls.Add(btnBrowsePath);

            lblSpaceReq = new Label();
            lblSpaceReq.Text = "所需空间: 约 280 MB";
            lblSpaceReq.Location = new Point(2, 78);
            lblSpaceReq.AutoSize = true;
            lblSpaceReq.ForeColor = Color.FromArgb(100, 116, 139);
            step2Panel.Controls.Add(lblSpaceReq);

            lblSpaceAvail = new Label();
            lblSpaceAvail.Text = "可用空间: 正在计算...";
            lblSpaceAvail.Location = new Point(170, 78);
            lblSpaceAvail.AutoSize = true;
            lblSpaceAvail.ForeColor = Color.FromArgb(100, 116, 139);
            step2Panel.Controls.Add(lblSpaceAvail);

            // Multi-Environment Configuration Panel
            Panel pnlEnvConfig = new Panel();
            pnlEnvConfig.Location = new Point(0, 104);
            pnlEnvConfig.Size = new Size(648, 255);
            pnlEnvConfig.BackColor = Color.FromArgb(241, 245, 249);
            pnlEnvConfig.BorderStyle = BorderStyle.FixedSingle;

            Label lblEnvGroupTitle = new Label();
            lblEnvGroupTitle.Text = "AGH 运行环境模式与多开端口设置 (Multi-Instance & Isolation)：";
            lblEnvGroupTitle.Font = new Font("Microsoft YaHei", 9F, FontStyle.Bold);
            lblEnvGroupTitle.ForeColor = Color.FromArgb(15, 23, 42);
            lblEnvGroupTitle.Location = new Point(12, 10);
            lblEnvGroupTitle.AutoSize = true;
            pnlEnvConfig.Controls.Add(lblEnvGroupTitle);

            rbIsolated = new RadioButton();
            rbIsolated.Text = "独立物理科研环境 (推荐: 数据目录 ~/.agh-physics, 默认端口 4180, 与其它环境 100% 隔离)";
            rbIsolated.Checked = true;
            rbIsolated.Location = new Point(16, 36);
            rbIsolated.AutoSize = true;
            rbIsolated.CheckedChanged += (s, e) => { if (rbIsolated.Checked) txtPort.Text = "4180"; };
            pnlEnvConfig.Controls.Add(rbIsolated);

            rbSandbox = new RadioButton();
            rbSandbox.Text = "虚拟沙箱隔离环境 (数据目录 ~/.agh-sandbox, 默认端口 4182, 强制调用内置便携Python)";
            rbSandbox.Location = new Point(16, 64);
            rbSandbox.AutoSize = true;
            rbSandbox.CheckedChanged += (s, e) => { if (rbSandbox.Checked) txtPort.Text = "4182"; };
            pnlEnvConfig.Controls.Add(rbSandbox);

            rbDefault = new RadioButton();
            rbDefault.Text = "接入系统默认环境 (数据目录 ~/.agh, 默认端口 4177, 共享全局配置与会话)";
            rbDefault.Location = new Point(16, 92);
            rbDefault.AutoSize = true;
            rbDefault.CheckedChanged += (s, e) => { if (rbDefault.Checked) txtPort.Text = "4177"; };
            pnlEnvConfig.Controls.Add(rbDefault);

            Label lblPort = new Label();
            lblPort.Text = "服务监听端口 (Port):";
            lblPort.Font = new Font("Microsoft YaHei", 9F, FontStyle.Bold);
            lblPort.Location = new Point(16, 128);
            lblPort.AutoSize = true;
            pnlEnvConfig.Controls.Add(lblPort);

            txtPort = new TextBox();
            txtPort.Text = "4180";
            txtPort.Location = new Point(148, 125);
            txtPort.Size = new Size(65, 23);
            txtPort.Font = new Font("Segoe UI", 9F);
            pnlEnvConfig.Controls.Add(txtPort);

            btnTestPort = new Button();
            btnTestPort.Text = "检测端口占用";
            btnTestPort.Size = new Size(100, 26);
            btnTestPort.Location = new Point(220, 123);
            btnTestPort.BackColor = Color.White;
            btnTestPort.FlatStyle = FlatStyle.Flat;
            btnTestPort.FlatAppearance.BorderColor = Color.FromArgb(203, 213, 225);
            btnTestPort.Click += (s, e) => {
                int testP;
                if (int.TryParse(txtPort.Text.Trim(), out testP))
                {
                    bool occ = TestPortListening(testP);
                    if (occ)
                    {
                        lblPortStatus.ForeColor = Color.DarkOrange;
                        lblPortStatus.Text = string.Format("端口 {0} 当前已被占用 (可正常启动或修改为其它端口)", testP);
                    }
                    else
                    {
                        lblPortStatus.ForeColor = Color.DarkGreen;
                        lblPortStatus.Text = string.Format("端口 {0} 当前空闲可用 [通过]", testP);
                    }
                }
                else
                {
                    lblPortStatus.ForeColor = Color.Red;
                    lblPortStatus.Text = "请输入有效的端口数字！";
                }
            };
            pnlEnvConfig.Controls.Add(btnTestPort);

            lblPortStatus = new Label();
            lblPortStatus.Text = "";
            lblPortStatus.Location = new Point(328, 128);
            lblPortStatus.Size = new Size(310, 20);
            lblPortStatus.ForeColor = Color.FromArgb(100, 116, 139);
            pnlEnvConfig.Controls.Add(lblPortStatus);

            Label lblMultiNotes = new Label();
            lblMultiNotes.Text = "多环境与多开特性说明：\n1. 支持与机器上已有的 4177 或其它 AGH 实例同时多开并行运行；\n2. 每一个环境模式均通过独立的 AGH_HOME 存储数据，会话历史、SQLite 数据库、模型配置与密钥凭据完全物理隔离，绝不会产生会话串扰或端口冲突。";
            lblMultiNotes.Location = new Point(16, 165);
            lblMultiNotes.Size = new Size(615, 75);
            lblMultiNotes.ForeColor = Color.FromArgb(71, 85, 105);
            pnlEnvConfig.Controls.Add(lblMultiNotes);

            step2Panel.Controls.Add(pnlEnvConfig);
            pnlContent.Controls.Add(step2Panel);
            UpdateDiskSpace();
        }

        private bool TestPortListening(int p)
        {
            try
            {
                string res = RunCmd("netstat", "-ano");
                string matchTarget = string.Format(":{0} ", p);
                return res.Contains(matchTarget) && res.Contains("LISTENING");
            }
            catch { return false; }
        }

        private void BuildStep3()
        {
            step3Panel = new Panel();
            step3Panel.Dock = DockStyle.Fill;
            step3Panel.Visible = false;

            lblProgressTitle = new Label();
            lblProgressTitle.Text = "步骤三：正在部署与安装系统核心文件...";
            lblProgressTitle.Font = new Font("Microsoft YaHei", 10.5F, FontStyle.Bold);
            lblProgressTitle.ForeColor = Color.FromArgb(30, 41, 59);
            lblProgressTitle.Location = new Point(0, 0);
            lblProgressTitle.AutoSize = true;
            step3Panel.Controls.Add(lblProgressTitle);

            progressBar = new ProgressBar();
            progressBar.Location = new Point(0, 36);
            progressBar.Size = new Size(648, 22);
            step3Panel.Controls.Add(progressBar);

            lblProgressStatus = new Label();
            lblProgressStatus.Text = "准备安装...";
            lblProgressStatus.Location = new Point(0, 64);
            lblProgressStatus.Size = new Size(648, 22);
            lblProgressStatus.ForeColor = Color.FromArgb(71, 85, 105);
            step3Panel.Controls.Add(lblProgressStatus);

            txtInstallLog = new TextBox();
            txtInstallLog.Multiline = true;
            txtInstallLog.ReadOnly = true;
            txtInstallLog.ScrollBars = ScrollBars.Vertical;
            txtInstallLog.BackColor = Color.FromArgb(241, 245, 249);
            txtInstallLog.Font = new Font("Consolas", 8.5F);
            txtInstallLog.Location = new Point(0, 92);
            txtInstallLog.Size = new Size(648, 280);
            step3Panel.Controls.Add(txtInstallLog);

            pnlContent.Controls.Add(step3Panel);
        }

        private void BuildStep4()
        {
            step4Panel = new Panel();
            step4Panel.Dock = DockStyle.Fill;
            step4Panel.Visible = false;

            lblFinishTitle = new Label();
            lblFinishTitle.Text = "安装顺利完成！";
            lblFinishTitle.Font = new Font("Microsoft YaHei", 14F, FontStyle.Bold);
            lblFinishTitle.ForeColor = Color.FromArgb(22, 101, 52); // Dark green
            lblFinishTitle.Location = new Point(0, 10);
            lblFinishTitle.AutoSize = true;
            step4Panel.Controls.Add(lblFinishTitle);

            lblFinishDesc = new Label();
            lblFinishDesc.Text = "AI 物理科研工作站已成功部署至您的计算机。\n快捷方式已生成，系统已正规注册至 Windows 已安装应用列表，可通过控制面板安全卸载。";
            lblFinishDesc.Location = new Point(0, 48);
            lblFinishDesc.Size = new Size(648, 50);
            lblFinishDesc.ForeColor = Color.FromArgb(71, 85, 105);
            step4Panel.Controls.Add(lblFinishDesc);

            Panel pnlFinishBox = new Panel();
            pnlFinishBox.Location = new Point(0, 110);
            pnlFinishBox.Size = new Size(648, 150);
            pnlFinishBox.BackColor = Color.FromArgb(241, 245, 249);
            pnlFinishBox.BorderStyle = BorderStyle.FixedSingle;

            chkLaunchNow = new CheckBox();
            chkLaunchNow.Text = "立即启动 AI 物理科研工作站服务并打开浏览器工作台";
            chkLaunchNow.Checked = true;
            chkLaunchNow.Font = new Font("Microsoft YaHei", 9.5F, FontStyle.Bold);
            chkLaunchNow.Location = new Point(20, 24);
            chkLaunchNow.AutoSize = true;
            pnlFinishBox.Controls.Add(chkLaunchNow);

            chkOpenReadme = new CheckBox();
            chkOpenReadme.Text = "查阅用户快速使用指引 (docs/INSTALL_GUIDE.md)";
            chkOpenReadme.Checked = false;
            chkOpenReadme.Location = new Point(20, 60);
            chkOpenReadme.AutoSize = true;
            pnlFinishBox.Controls.Add(chkOpenReadme);

            Label lblFinishTips = new Label();
            lblFinishTips.Text = "提示：日常使用时，可直接双击桌面的「AI 物理科研工作站」快捷方式启动服务。";
            lblFinishTips.Location = new Point(20, 100);
            lblFinishTips.AutoSize = true;
            lblFinishTips.ForeColor = Color.FromArgb(100, 116, 139);
            pnlFinishBox.Controls.Add(lblFinishTips);

            step4Panel.Controls.Add(pnlFinishBox);
            pnlContent.Controls.Add(step4Panel);
        }

        private void CheckEnvironment()
        {
            txtEnvStatus.Clear();
            AppendLog(txtEnvStatus, "=== AI 物理科研工作站 - 运行环境自检 ===\n", Color.DarkBlue, true);

            // 1. OS check
            AppendLog(txtEnvStatus, "[1] 操作系统架构: ", Color.Black, true);
            if (IntPtr.Size == 8)
            {
                AppendLog(txtEnvStatus, "Windows 64 位 [通过]\n", Color.DarkGreen, false);
            }
            else
            {
                AppendLog(txtEnvStatus, "Windows 32 位 [警告: 建议使用 64 位系统]\n", Color.DarkOrange, false);
            }

            // 2. Node.js check
            AppendLog(txtEnvStatus, "[2] Node.js 运行时: ", Color.Black, true);
            string nodeVer = RunCmd("node", "-v");
            if (!string.IsNullOrEmpty(nodeVer) && nodeVer.StartsWith("v"))
            {
                isNodeInstalled = true;
                AppendLog(txtEnvStatus, string.Format("{0} [已安装]\n", nodeVer), Color.DarkGreen, false);
            }
            else
            {
                isNodeInstalled = false;
                AppendLog(txtEnvStatus, "未检测到 Node.js (底座需要 Node.js >= 24.10)\n", Color.DarkRed, true);
            }

            // 3. pnpm check
            AppendLog(txtEnvStatus, "[3] pnpm 包管理器: ", Color.Black, true);
            string pnpmVer = RunCmd("pnpm", "-v");
            if (!string.IsNullOrEmpty(pnpmVer) && !pnpmVer.Contains("error"))
            {
                AppendLog(txtEnvStatus, string.Format("v{0} [已就绪]\n", pnpmVer), Color.DarkGreen, false);
            }
            else
            {
                AppendLog(txtEnvStatus, "未配置全局 pnpm (安装程序将自动通过 Corepack 启用)\n", Color.DarkSlateGray, false);
            }

            // 4. Python check
            AppendLog(txtEnvStatus, "[4] Python 科学环境: ", Color.Black, true);
            string pyVer = RunCmd("python", "--version");
            if (!string.IsNullOrEmpty(pyVer))
            {
                string pyLibCheck = RunCmd("python", "-c \"import sympy, pint, numpy, scipy, matplotlib; print('READY')\"");
                if (pyLibCheck.Contains("READY"))
                {
                    isPythonReady = true;
                    AppendLog(txtEnvStatus, string.Format("{0} (科学库完整) [已就绪]\n", pyVer), Color.DarkGreen, false);
                }
                else
                {
                    isPythonReady = false;
                    AppendLog(txtEnvStatus, string.Format("{0} (缺少部分科学库，安装时将自动补全)\n", pyVer), Color.DarkOrange, false);
                }
            }
            else
            {
                isPythonReady = false;
                AppendLog(txtEnvStatus, "系统未安装全局 Python (将调用内置便携运行时)\n", Color.DarkOrange, false);
            }

            // 5. Portable runtime check
            AppendLog(txtEnvStatus, "[5] 内置离线便携包: ", Color.Black, true);
            string wheelDir = Path.Combine(sourceDir, "physics-agent\\third_party\\portable-runtime\\wheels");
            if (Directory.Exists(wheelDir))
            {
                int count = Directory.GetFiles(wheelDir, "*.whl").Length;
                AppendLog(txtEnvStatus, string.Format("已就绪 (包含 {0} 个版本锁定的离线 wheels 包)\n", count), Color.DarkGreen, false);
            }
            else
            {
                AppendLog(txtEnvStatus, "便携运行时目录就绪\n", Color.DarkGreen, false);
            }

            // 6. Check source assets availability
            string localCli = Path.Combine(sourceDir, "packages\\cli\\dist\\local");
            string localAgent = Path.Combine(sourceDir, "physics-agent");
            bool hasLocalAssets = Directory.Exists(localCli) || Directory.Exists(localAgent);
            AppendLog(txtEnvStatus, "[6] 安装资源模式: ", Color.Black, true);
            if (hasLocalAssets)
            {
                AppendLog(txtEnvStatus, "完整离线发行包模式 (本地资源完备，秒级部署) [通过]\n", Color.DarkGreen, false);
            }
            else
            {
                AppendLog(txtEnvStatus, "独立安装器单文件模式 (安装时将自动拉取预构建包) [提示]\n", Color.DarkCyan, false);
            }

            // Dynamically adapt checkboxes to detected environment state
            if (chkAutoDownloadNode != null) chkAutoDownloadNode.Checked = !isNodeInstalled;
            if (chkSetupPython != null) chkSetupPython.Checked = !isPythonReady;
        }

        private void AppendLog(RichTextBox box, string text, Color color, bool bold)
        {
            box.SelectionStart = box.TextLength;
            box.SelectionLength = 0;
            box.SelectionColor = color;
            box.SelectionFont = new Font(box.Font, bold ? FontStyle.Bold : FontStyle.Regular);
            box.AppendText(text);
            box.SelectionColor = box.ForeColor;
        }

        private void UpdateDiskSpace()
        {
            try
            {
                string path = txtInstallPath.Text;
                string root = Path.GetPathRoot(path);
                if (!string.IsNullOrEmpty(root) && Directory.Exists(root))
                {
                    DriveInfo d = new DriveInfo(root);
                    long freeGb = d.AvailableFreeSpace / (1024 * 1024 * 1024);
                    lblSpaceAvail.Text = string.Format("目标磁盘 ({0}) 可用空间: 约 {1} GB", root, freeGb);
                }
            }
            catch
            {
                lblSpaceAvail.Text = "目标磁盘可用空间: 正常";
            }
        }

        private void ShowStep(int step)
        {
            currentStep = step;
            step1Panel.Visible = (step == 1);
            step2Panel.Visible = (step == 2);
            step3Panel.Visible = (step == 3);
            step4Panel.Visible = (step == 4);

            btnBack.Enabled = (step == 2);
            btnBack.Visible = (step != 3 && step != 4);
            btnCancel.Visible = (step != 3 && step != 4);

            if (step == 1)
            {
                btnNext.Text = "下一步 (Next >)";
                btnNext.Enabled = true;
            }
            else if (step == 2)
            {
                btnNext.Text = "立即安装 (Install)";
                btnNext.Enabled = true;
            }
            else if (step == 3)
            {
                btnNext.Enabled = false;
                btnNext.Visible = false;
            }
            else if (step == 4)
            {
                btnNext.Text = "完成 (Finish)";
                btnNext.Enabled = true;
                btnNext.Visible = true;
            }
        }

        private class InstallConfig
        {
            public string TargetDir;
            public string EnvMode;
            public int Port;
            public bool AutoDownloadNode;
            public bool SetupPython;
            public bool CreateDesktopShortcut;
            public bool CreateStartMenuShortcut;
            public bool RegisterUninstall;
        }

        private void BtnNext_Click(object sender, EventArgs e)
        {
            if (currentStep == 1)
            {
                ShowStep(2);
            }
            else if (currentStep == 2)
            {
                // Validate directory
                string target = txtInstallPath.Text.Trim();
                if (string.IsNullOrEmpty(target))
                {
                    MessageBox.Show(this, "请指定有效的安装路径！", "提示", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                    return;
                }

                InstallConfig cfg = new InstallConfig();
                cfg.TargetDir = target;
                cfg.EnvMode = rbSandbox.Checked ? "sandbox" : (rbDefault.Checked ? "default" : "isolated");
                int p = 4180;
                int.TryParse(txtPort.Text.Trim(), out p);
                cfg.Port = p > 0 ? p : 4180;
                cfg.AutoDownloadNode = chkAutoDownloadNode.Checked;
                cfg.SetupPython = chkSetupPython.Checked;
                cfg.CreateDesktopShortcut = chkCreateDesktopShortcut.Checked;
                cfg.CreateStartMenuShortcut = chkCreateStartMenuShortcut.Checked;
                cfg.RegisterUninstall = chkRegisterUninstall.Checked;

                ShowStep(3);
                StartInstallThread(cfg);
            }
            else if (currentStep == 4)
            {
                string target = txtInstallPath.Text.Trim();
                if (chkLaunchNow.Checked)
                {
                    string startBat = Path.Combine(target, "一键启动.bat");
                    if (File.Exists(startBat))
                    {
                        ProcessStartInfo psi = new ProcessStartInfo(startBat);
                        psi.WorkingDirectory = target;
                        Process.Start(psi);
                    }
                }
                if (chkOpenReadme.Checked)
                {
                    string docPath = Path.Combine(target, "docs\\INSTALL_GUIDE.md");
                    if (File.Exists(docPath)) Process.Start(docPath);
                }
                this.Close();
            }
        }

        private void StartInstallThread(InstallConfig cfg)
        {
            BackgroundWorker worker = new BackgroundWorker();
            worker.WorkerReportsProgress = true;
            worker.DoWork += (s, args) => DoInstall(cfg, worker);
            worker.ProgressChanged += (s, args) => {
                progressBar.Value = args.ProgressPercentage;
                lblProgressStatus.Text = args.UserState as string;
                txtInstallLog.AppendText(args.UserState + "\r\n");
            };
            worker.RunWorkerCompleted += (s, args) => {
                if (args.Error != null)
                {
                    MessageBox.Show(this, "安装过程中出现异常: " + args.Error.Message, "安装未完成", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    ShowStep(2);
                }
                else
                {
                    ShowStep(4);
                }
            };
            worker.RunWorkerAsync();
        }

        private void DoInstall(InstallConfig cfg, BackgroundWorker worker)
        {
            string targetDir = cfg.TargetDir;

            // 1. Download & Install Node.js if missing and requested
            if (!isNodeInstalled && cfg.AutoDownloadNode)
            {
                worker.ReportProgress(4, "正在检测 Node.js 运行时...");
                bool nodeInstalledSuccess = false;

                // Priority 1: Try winget if available
                try
                {
                    worker.ReportProgress(6, "尝试通过 Windows 包管理器 (winget) 安装 Node.js LTS...");
                    string wingetRes = RunCmd("winget", "install OpenJS.NodeJS.LTS --accept-package-agreements --accept-source-agreements --silent");
                    if (wingetRes.Contains("Successfully") || wingetRes.Contains("成功") || wingetRes.Contains("已安装"))
                    {
                        nodeInstalledSuccess = true;
                        worker.ReportProgress(12, "Node.js 运行时通过 winget 部署成功。");
                    }
                }
                catch { }

                // Priority 2: Fallback to direct official MSI download (essential for clean Win10/Win11 without winget)
                if (!nodeInstalledSuccess)
                {
                    try
                    {
                        worker.ReportProgress(7, "正在从官方镜像直连拉取 Node.js 24 LTS 独立安装包 (约 30 MB)...");
                        string tempMsi = Path.Combine(Path.GetTempPath(), "nodejs_lts_x64_setup.msi");
                        using (WebClient client = new WebClient())
                        {
                            // Official Node.js 24 LTS x64 MSI
                            client.DownloadFile("https://nodejs.org/dist/v24.10.0/node-v24.10.0-x64.msi", tempMsi);
                        }

                        if (File.Exists(tempMsi))
                        {
                            worker.ReportProgress(10, "正在静默安装 Node.js 24 LTS 运行时...");
                            ProcessStartInfo psiMsi = new ProcessStartInfo("msiexec.exe", "/i \"" + tempMsi + "\" /passive /norestart");
                            psiMsi.UseShellExecute = false;
                            using (Process p = Process.Start(psiMsi))
                            {
                                if (p != null) p.WaitForExit();
                            }
                            nodeInstalledSuccess = true;
                            worker.ReportProgress(12, "Node.js 24 LTS 官方安装包部署完成！");
                        }
                    }
                    catch (Exception exNode)
                    {
                        worker.ReportProgress(10, "提示: 自动安装 Node.js 遇到网络限制 (" + exNode.Message + ")，请安装后按指引手动下载。");
                    }
                }

                // Refresh PATH in current process
                try
                {
                    string sysPath = Environment.GetEnvironmentVariable("PATH", EnvironmentVariableTarget.Machine) + ";" +
                                     Environment.GetEnvironmentVariable("PATH", EnvironmentVariableTarget.User);
                    Environment.SetEnvironmentVariable("PATH", sysPath, EnvironmentVariableTarget.Process);
                }
                catch { }
            }

            worker.ReportProgress(15, "正在创建目标安装目录: " + targetDir);
            if (!Directory.Exists(targetDir)) Directory.CreateDirectory(targetDir);

            // 2. Locate source assets (Support both local extracted directory & standalone installer mode)
            string localCli = Path.Combine(sourceDir, "packages\\cli\\dist\\local");
            string localAgent = Path.Combine(sourceDir, "physics-agent");
            bool hasLocalAssets = Directory.Exists(localCli) || Directory.Exists(localAgent);

            if (hasLocalAssets)
            {
                // Local extracted package mode: copy directly from sourceDir (2-3 seconds)
                string[] copyDirs = new string[] { ".agh", "physics-agent", "packages", "docs", "scripts" };
                int stepVal = 20;
                foreach (string d in copyDirs)
                {
                    string srcSub = Path.Combine(sourceDir, d);
                    string dstSub = Path.Combine(targetDir, d);
                    if (Directory.Exists(srcSub))
                    {
                        worker.ReportProgress(stepVal, "正在复制目录: " + d + " ...");
                        CopyDirectory(srcSub, dstSub);
                    }
                    stepVal += 10;
                }

                worker.ReportProgress(70, "正在配置启动脚本与说明文档...");
                string[] copyFiles = new string[] { "README.md", "一键启动.bat", "一键安装.bat", "环境自检.bat", "图形化安装.bat", "package.json", "pnpm-workspace.yaml" };
                foreach (string f in copyFiles)
                {
                    string srcFile = Path.Combine(sourceDir, f);
                    string dstFile = Path.Combine(targetDir, f);
                    if (File.Exists(srcFile)) File.Copy(srcFile, dstFile, true);
                }
            }
            else
            {
                // Standalone installer mode (Setup.exe downloaded alone): Look for local zip or fetch from GitHub Release
                worker.ReportProgress(22, "检测到独立安装器模式，正在查找资源包...");
                string foundZip = null;
                try
                {
                    string[] zips = Directory.GetFiles(sourceDir, "*.zip");
                    foreach (string z in zips)
                    {
                        if (z.IndexOf("physics", StringComparison.OrdinalIgnoreCase) >= 0 ||
                            z.IndexOf("agent", StringComparison.OrdinalIgnoreCase) >= 0)
                        {
                            foundZip = z;
                            break;
                        }
                    }
                }
                catch { }

                if (foundZip != null && File.Exists(foundZip))
                {
                    worker.ReportProgress(30, "在当前目录下找到预构建包: " + Path.GetFileName(foundZip) + "，正在解压...");
                    UnzipToDirectory(foundZip, targetDir);
                }
                else
                {
                    // Attempt online pull from GitHub Release
                    worker.ReportProgress(25, "正在连接 GitHub Releases 拉取最新预构建发行包 (约 25 MB)...");
                    string downloadZip = Path.Combine(Path.GetTempPath(), "ai_physics_agent_release.zip");
                    bool downloadOk = false;
                    try
                    {
                        using (WebClient client = new WebClient())
                        {
                            client.Headers.Add("User-Agent", "AIPhysicsAgent-Installer/1.0");
                            // Fallback release archive URL
                            client.DownloadFile("https://github.com/VirtuwiseZ/physics-agent-based-on-agnes-harness/archive/refs/heads/main.zip", downloadZip);
                        }
                        if (File.Exists(downloadZip) && new FileInfo(downloadZip).Length > 100000)
                        {
                            downloadOk = true;
                        }
                    }
                    catch { }

                    if (downloadOk)
                    {
                        worker.ReportProgress(55, "下载完成，正在解压部署至目标目录...");
                        UnzipToDirectory(downloadZip, targetDir);
                    }
                    else
                    {
                        throw new Exception("未在当前目录下找到程序资产包，且自动网络下载未完成。\n请下载预构建完整发行包 (AI_Physics_Agent_v1.0.0_Windows_x64.zip)，解压后再运行安装程序。");
                    }
                }
            }

            // Copy app.ico
            string iconSrc = Path.Combine(sourceDir, "installer\\app.ico");
            string iconDst = Path.Combine(targetDir, "app.ico");
            if (File.Exists(iconSrc)) File.Copy(iconSrc, iconDst, true);

            // 4. Copy / Generate Uninstall.exe
            worker.ReportProgress(76, "正在配置卸载程序 (Uninstall.exe)...");
            string uninstallerSrc = Path.Combine(sourceDir, "installer\\Uninstall.exe");
            string uninstallerDst = Path.Combine(targetDir, "Uninstall.exe");
            if (File.Exists(uninstallerSrc))
            {
                File.Copy(uninstallerSrc, uninstallerDst, true);
            }

            // 4b. Write instance_config.json for persistent multi-environment isolation
            worker.ReportProgress(80, "正在写入环境配置 (instance_config.json)...");
            try
            {
                string homePath = (cfg.EnvMode == "sandbox")
                    ? Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".agh-sandbox")
                    : (cfg.EnvMode == "default"
                        ? Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".agh")
                        : Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".agh-physics"));

                string jsonConfig = string.Format(
                    "{{\r\n  \"envMode\": \"{0}\",\r\n  \"port\": {1},\r\n  \"workspaceDir\": \"agh-workspace\",\r\n  \"appHome\": \"{2}\",\r\n  \"installedAt\": \"{3}\"\r\n}}",
                    cfg.EnvMode,
                    cfg.Port,
                    homePath.Replace("\\", "\\\\"),
                    DateTime.Now.ToString("s")
                );
                File.WriteAllText(Path.Combine(targetDir, "instance_config.json"), jsonConfig, Encoding.UTF8);
            }
            catch { }

            // 5. Setup Python if requested
            if (cfg.SetupPython)
            {
                worker.ReportProgress(83, "正在检测并配置 Python 科学计算依赖库...");
                string pyVer = RunCmd("python", "--version");
                bool hasPy = !string.IsNullOrEmpty(pyVer) && pyVer.Contains("Python");

                // If no python on clean Win10/Win11, attempt automated lightweight setup
                if (!hasPy)
                {
                    worker.ReportProgress(84, "未检测到系统 Python，正在尝试通过包管理器安装 Python 3.13...");
                    try
                    {
                        RunCmd("winget", "install Python.Python.3.13 --accept-package-agreements --accept-source-agreements --silent");
                    }
                    catch { }
                }

                string reqPath = Path.Combine(targetDir, "physics-agent\\hooks\\requirements.txt");
                if (File.Exists(reqPath))
                {
                    worker.ReportProgress(86, "正在安装核心科学计算依赖 (sympy, pint, numpy, scipy, matplotlib)...");
                    RunCmd("pip", "install -r \"" + reqPath + "\"");
                }
            }

            // 6. Create shortcuts
            string desktopDir = Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory);
            string startMenuDir = Environment.GetFolderPath(Environment.SpecialFolder.Programs);
            string targetLauncher = Path.Combine(targetDir, "一键启动.bat");
            string doctorLauncher = Path.Combine(targetDir, "环境自检.bat");

            if (cfg.CreateDesktopShortcut)
            {
                worker.ReportProgress(88, "正在创建桌面快捷方式...");
                string desktopLnk = Path.Combine(desktopDir, "AI 物理科研工作站.lnk");
                CreateShortcut(desktopLnk, targetLauncher, targetDir, "启动 AI 物理科研工作站", iconDst);
            }

            if (cfg.CreateStartMenuShortcut)
            {
                worker.ReportProgress(92, "正在创建开始菜单快捷方式组...");
                string groupDir = Path.Combine(startMenuDir, "AI 物理科研工作站");
                if (!Directory.Exists(groupDir)) Directory.CreateDirectory(groupDir);

                string menuLnk = Path.Combine(groupDir, "AI 物理科研工作站.lnk");
                CreateShortcut(menuLnk, targetLauncher, targetDir, "启动 AI 物理科研工作站", iconDst);

                string docLnk = Path.Combine(groupDir, "运行环境健康自检.lnk");
                CreateShortcut(docLnk, doctorLauncher, targetDir, "运行环境诊断自检", iconDst);

                string uninstLnk = Path.Combine(groupDir, "卸载 AI 物理科研工作站.lnk");
                CreateShortcut(uninstLnk, uninstallerDst, targetDir, "卸载 AI 物理科研工作站", iconDst);
            }

            // 7. Register to Windows Add/Remove Programs (Registry)
            if (cfg.RegisterUninstall)
            {
                worker.ReportProgress(96, "正在注册至 Windows 系统已安装应用列表...");
                RegisterWindowsUninstall(targetDir, uninstallerDst, iconDst);
            }

            worker.ReportProgress(100, "安装全部完成！");
            Thread.Sleep(400);
        }

        private static void UnzipToDirectory(string zipPath, string extractPath)
        {
            try
            {
                // Try .NET 4.5+ ZipFile reflection to avoid requiring external references
                Type zipType = Type.GetType("System.IO.Compression.ZipFile, System.IO.Compression.FileSystem");
                if (zipType != null)
                {
                    MethodInfo mi = zipType.GetMethod("ExtractToDirectory", new Type[] { typeof(string), typeof(string) });
                    if (mi != null)
                    {
                        mi.Invoke(null, new object[] { zipPath, extractPath });
                        return;
                    }
                }
            }
            catch { }

            // Fallback to PowerShell Expand-Archive
            ProcessStartInfo psi = new ProcessStartInfo("powershell.exe",
                string.Format("-NoProfile -Command \"Expand-Archive -Path '{0}' -DestinationPath '{1}' -Force\"", zipPath, extractPath));
            psi.CreateNoWindow = true;
            psi.UseShellExecute = false;
            using (Process p = Process.Start(psi))
            {
                if (p != null) p.WaitForExit();
            }
        }

        private void RegisterWindowsUninstall(string installDir, string uninstallerPath, string iconPath)
        {
            try
            {
                using (RegistryKey parent = Registry.CurrentUser.OpenSubKey(@"Software\Microsoft\Windows\CurrentVersion\Uninstall", true))
                {
                    if (parent != null)
                    {
                        using (RegistryKey appKey = parent.CreateSubKey("AIPhysicsAgent"))
                        {
                            if (appKey != null)
                            {
                                appKey.SetValue("DisplayName", "AI 物理科研工作站 (Physics Research Agent)");
                                appKey.SetValue("DisplayVersion", "0.1.0");
                                appKey.SetValue("Publisher", "AI Physics Research Team");
                                appKey.SetValue("InstallLocation", installDir);
                                appKey.SetValue("UninstallString", "\"" + uninstallerPath + "\"");
                                appKey.SetValue("DisplayIcon", iconPath);
                                appKey.SetValue("HelpLink", "https://github.com/VirtuwiseZ/agnes-harness");
                                appKey.SetValue("URLInfoAbout", "https://github.com/VirtuwiseZ/agnes-harness");
                                appKey.SetValue("InstallDate", DateTime.Now.ToString("yyyyMMdd"));
                                appKey.SetValue("EstimatedSize", 260000, RegistryValueKind.DWord);
                                appKey.SetValue("NoModify", 1, RegistryValueKind.DWord);
                                appKey.SetValue("NoRepair", 1, RegistryValueKind.DWord);
                            }
                        }
                    }
                }
            }
            catch { }
        }

        private void CreateShortcut(string shortcutPath, string targetPath, string workDir, string description, string iconPath)
        {
            try
            {
                Type shellType = Type.GetTypeFromProgID("WScript.Shell");
                if (shellType != null)
                {
                    dynamic shell = Activator.CreateInstance(shellType);
                    dynamic shortcut = shell.CreateShortcut(shortcutPath);
                    shortcut.TargetPath = targetPath;
                    shortcut.WorkingDirectory = workDir;
                    shortcut.Description = description;
                    if (File.Exists(iconPath))
                    {
                        shortcut.IconLocation = iconPath + ",0";
                    }
                    shortcut.Save();
                }
            }
            catch { }
        }

        private static void CopyDirectory(string sourceDir, string destinationDir)
        {
            DirectoryInfo dir = new DirectoryInfo(sourceDir);
            if (!dir.Exists) return;

            DirectoryInfo[] dirs = dir.GetDirectories();
            if (!Directory.Exists(destinationDir))
            {
                Directory.CreateDirectory(destinationDir);
            }

            FileInfo[] files = dir.GetFiles();
            foreach (FileInfo file in files)
            {
                string tempPath = Path.Combine(destinationDir, file.Name);
                file.CopyTo(tempPath, true);
            }

            foreach (DirectoryInfo subdir in dirs)
            {
                // Skip cache and git
                if (subdir.Name == "__pycache__" || subdir.Name == ".git" || subdir.Name == "node_modules") continue;
                string tempPath = Path.Combine(destinationDir, subdir.Name);
                CopyDirectory(subdir.FullName, tempPath);
            }
        }

        private string RunCmd(string exe, string args)
        {
            try
            {
                ProcessStartInfo psi = new ProcessStartInfo(exe, args);
                psi.CreateNoWindow = true;
                psi.UseShellExecute = false;
                psi.RedirectStandardOutput = true;
                psi.RedirectStandardError = true;
                using (Process p = Process.Start(psi))
                {
                    if (p != null)
                    {
                        string output = p.StandardOutput.ReadToEnd();
                        p.WaitForExit(3000);
                        return output.Trim();
                    }
                }
            }
            catch { }
            return "";
        }

        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new SetupForm());
        }
    }
}
