# **ArchImmich**

[![GitHub stars](https://img.shields.io/github/stars/osa911/archimmich)](https://github.com/osa911/archimmich/stargazers)
**ArchImmich** is a modern export and archive tool designed for users of the Immich platform. This application simplifies the process of fetching media buckets and exporting them into archives, all while offering a sleek and user-friendly interface.

---

## **Features**

- **Fetch Media Buckets**:
  Retrieve buckets of media files grouped by day or month.

- **Customizable Export Options**:

  - Archive size configuration.
  - Group files into single or multiple archives.

- **Real-Time Progress**:

  - General and per-download progress bars.
  - Logs for detailed insights.

- **Integrity Validation**:

  - Check existing archives to avoid redundant downloads.

- **User-Friendly Interface**:
  - Modern UI with intuitive options for configuration and archive management.

---

## **Installation**

### **1. Clone the Repository**

```bash
git clone https://github.com/osa911/archimmich.git
cd archimmich
```

### **2. Install Dependencies**

Make sure you have **Python 3.7 or higher** installed. Then, set up your virtual environment and install the required packages:

1. **Create a virtual environment**:

   ```bash
   python3 -m venv venv
   ```

2. **Activate the virtual environment**:

   - **macOS/Linux**:
     ```bash
     source venv/bin/activate
     ```
   - **Windows**:
     ```bash
     venv\\Scripts\\activate
     ```

3. **Install the required packages**:
   ```bash
   pip install -r requirements.txt
   ```

If the `requirements.txt` file is missing or incomplete, manually install the necessary libraries:

```bash
pip install PyQt5 requests tqdm
```

### **3. Run the Application**

Start the application with:

```bash
python3 archimmich.py
```

---

## **Building the Executable**

To package the application into a standalone executable:

1. **Install PyInstaller**:

   ```bash
   pip install pyinstaller
   ```

2. **Build the Executable**:

   ```bash
   pyinstaller --onefile --icon=your_icon.ico archimmich.py
   ```

3. The executable will be available in the `dist` folder.

---

## **Usage**

1. **Login**:

   - Enter your **API key** and **server URL**.
   - Click **Login** to authenticate with the Immich server.

2. **Configure Export**:

   - Choose archive size, grouping (day/month), and the output directory.

3. **Fetch Buckets**:

   - Click **Fetch Buckets** to list available media buckets.
   - Select the desired buckets for export.

4. **Export**:

   - Start the export process and monitor progress in the logs and progress bars.

5. **Access Archives**:
   - Use the **Open Folder** button to access exported archives.

---

## **Screenshots**

_Add screenshots here to showcase the UI and features._

---

## **Contributing**

1. Fork the repository.
2. Create a new feature branch:
   ```bash
   git checkout -b feature-name
   ```
3. Commit your changes:
   ```bash
   git commit -m "Add feature-name"
   ```
4. Push to the branch:
   ```bash
   git push origin feature-name
   ```
5. Open a pull request.

---

## **License**

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information.

---

## **Contact**

For feedback, issues, or questions:

- **GitHub Issues**: [https://github.com/osa911/archimmich/issues](https://github.com/osa911/archimmich/issues)

## License

MIT

## Author

[Osa911](https://github.com/osa911)
