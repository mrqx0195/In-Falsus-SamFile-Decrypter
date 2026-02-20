# In Falsus SamFile Decrypter

一个用于解密/加密《In Falsus》部分资源文件的工具。

当前支持版本：试玩版 V0.2.2 - [c56e1d111]

## [decrypt.py](./decrypt.py)

**依赖：`pip install cryptography`**

### 用法

用于解密或加密游戏资源文件，支持单个文件或批量处理。

#### 命令行参数
- `mode`：必需，操作模式，必须为 `decrypt`（解密）或 `encrypt`（加密）。
- `input`：必需，输入文件或目录路径。
- `output`：必需，输出文件或目录路径。
- `--batch`：可选标志，启用批量处理模式。当指定此标志时，`input` 和 `output` 应视为目录。

#### 示例
1. 解密单个文件：
   ```bash
   python decrypt.py decrypt encrypted.file decrypted.file
   ```
2. 批量解密目录中的所有文件：
   ```bash
   python decrypt.py decrypt ./encrypted_folder ./decrypted_folder --batch
   ```
3. 加密单个文件：
   ```bash
   python decrypt.py encrypt decrypted.file encrypted.file
   ```

## [rename_assets.py](./rename_assets.py)

### 用法

用于将解密后的文件（以 GUID 命名）重命名为游戏原本的资源路径。需要预先准备的映射文件。

#### 命令行参数
- `input_dir`：必需，解密文件所在的目录（例如 `./output`）。  
- `--mappings`：映射文件路径。默认值为 [`mappings.txt`](./mappings.txt)。

#### 示例
```bash
python rename_assets.py ./output --mappings mappings.txt
```