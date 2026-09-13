import os
import sys
import re
import math
from collections import Counter


# ============================================================
# DOS — OVERALL ARCHITECTURE SCORE
# ============================================================
#
# SCAN SCOPE:
#
#   DOS/
#   ├── everything in DOS root
#   └── projects/
#       └── everything recursively
#
# PURPOSE:
#
#   Measure the overall amount of real engineering contained
#   inside the DOS system.
#
# SCORE REWARDS:
#
#   • More real code
#   • More functions
#   • More classes
#   • More branches
#   • More loops
#   • More decisions
#   • More nesting
#   • More algorithms
#   • More modules
#   • More data operations
#   • More API/network operations
#   • More async/concurrent logic
#   • More information-dense code
#
# THIS IS NOT A COMPETITION.
#
# There is only one score:
#
#       YOUR DOS OVERALL SCORE
#
# ============================================================


# ============================================================
# CODE EXTENSIONS
# ============================================================

CODE_EXTENSIONS = {

    # Web
    '.js': 'JavaScript',
    '.jsx': 'JavaScript React',
    '.mjs': 'JavaScript',
    '.cjs': 'JavaScript',

    '.ts': 'TypeScript',
    '.tsx': 'TypeScript React',
    '.mts': 'TypeScript',
    '.cts': 'TypeScript',

    '.vue': 'Vue',
    '.svelte': 'Svelte',

    '.html': 'HTML',
    '.htm': 'HTML',

    '.css': 'CSS',
    '.scss': 'SCSS',
    '.sass': 'Sass',
    '.less': 'Less',

    # Python
    '.py': 'Python',
    '.pyw': 'Python',

    # C / C++
    '.c': 'C',
    '.h': 'C Header',
    '.cpp': 'C++',
    '.cc': 'C++',
    '.cxx': 'C++',
    '.hpp': 'C++ Header',
    '.hh': 'C++ Header',
    '.hxx': 'C++ Header',

    # JVM
    '.java': 'Java',
    '.kt': 'Kotlin',
    '.kts': 'Kotlin Script',
    '.scala': 'Scala',

    # Backend
    '.cs': 'C#',
    '.go': 'Go',
    '.rs': 'Rust',
    '.rb': 'Ruby',
    '.php': 'PHP',
    '.swift': 'Swift',
    '.dart': 'Dart',

    # Functional
    '.ex': 'Elixir',
    '.exs': 'Elixir Script',
    '.erl': 'Erlang',
    '.hrl': 'Erlang Header',
    '.hs': 'Haskell',

    # Data
    '.sql': 'SQL',
    '.r': 'R',

    # Scripts
    '.sh': 'Shell',
    '.bash': 'Bash',
    '.ps1': 'PowerShell',
    '.lua': 'Lua',
    '.pl': 'Perl',
    '.pm': 'Perl Module',

    # Infrastructure
    '.tf': 'Terraform',
    '.hcl': 'HCL',
    '.proto': 'Protocol Buffers',
    '.graphql': 'GraphQL',
    '.gql': 'GraphQL',
    '.asm': 'Assembly',
    '.s': 'Assembly',
}


SPECIAL_FILES = {
    'dockerfile': 'Docker',
    'makefile': 'Make',
    'jenkinsfile': 'Jenkins',
    'cmakelists.txt': 'CMake',
}


DOC_EXTENSIONS = {
    '.md',
    '.txt',
    '.rst',
    '.adoc',
    '.asciidoc',
    '.tex',
}


# ============================================================
# DIRECTORIES TO IGNORE
# ============================================================

SKIP_DIRS = {
    '.git',
    '.svn',
    '.hg',

    'node_modules',

    'dist',
    'build',
    'out',

    'coverage',

    '.next',
    '.nuxt',
    '.svelte-kit',

    '.turbo',
    '.vercel',

    'target',
    'obj',
    'bin',

    'venv',
    '.venv',

    '__pycache__',

    '.pytest_cache',
    '.mypy_cache',

    '.gradle',
    '.idea',
    '.vscode',

    'vendor',

    'pods',

    '.dart_tool',

    '.terraform',

    'site-packages',

    'egg-info',
}


# ============================================================
# COMPLEXITY PATTERNS
# ============================================================

PATTERNS = {

    # Decisions
    'branch':
        r'\b(if|elif|else|unless|switch|case|when|match)\b',

    # Loops
    'loop':
        r'\b(for|while|foreach|loop|do)\b',

    # Functions
    'function':
        r'\b(function|def|fn|func|fun|lambda)\b',

    # Classes
    'class':
        r'\b(class|struct|interface|trait|record|enum)\b',

    # Exceptions
    'exception':
        r'\b(try|catch|except|finally|raise|throw|rescue)\b',

    # Boolean complexity
    'boolean':
        r'&&|\|\||\band\b|\bor\b|\bnot\b|!',

    # Comparisons
    'comparison':
        r'===|!==|==|!=|<=|>=|<|>',

    # Assignment
    'assignment':
        r'(?<![=!<>])=(?!=)|\+=|-=|\*=|/=|%=|:=',

    # Arithmetic
    'arithmetic':
        r'\+|-|\*|/|%|\*\*',

    # Bitwise
    'bitwise':
        r'<<|>>|&|\||\^|~',

    # Ternary
    'ternary':
        r'\?.*?:',

    # Optional chaining
    'optional_chain':
        r'\?\.\w+',

    # Nullish
    'nullish':
        r'\?\?',

    # Arrow functions
    'arrow':
        r'=>',

    # Async
    'async':
        r'\b(async|await|promise|future|coroutine)\b',

    # Generators
    'generator':
        r'\byield\b',

    # Imports
    'import':
        r'\b(import|from|require|include|using|use|load|library)\b',

    # Calls
    'call':
        r'\b[A-Za-z_][A-Za-z0-9_]*\s*\(',

    # Method chains
    'chain':
        r'\.\w+\s*\(',

    # Decorators
    'decorator':
        r'(?m)^\s*@\w+',

    # Generics
    'generic':
        r'<[A-Za-z_][A-Za-z0-9_, <>]*>',

    # Network
    'network':
        r'\b(fetch|axios|http|https|request|response|socket|websocket|graphql)\b',

    # Database
    'database':
        r'\b(database|db|query|mongoose|sequelize|prisma|typeorm|postgres|mysql|mongodb|redis)\b',

    # Concurrency
    'concurrency':
        r'\b(thread|mutex|lock|atomic|parallel|concurrent|channel|goroutine)\b',

    # Regex
    'regex':
        r'/[^/\n]+/[gimsuy]*',

    # SQL
    'sql':
        r'\b(SELECT|INSERT|UPDATE|DELETE|JOIN|UNION|GROUP\s+BY|ORDER\s+BY|HAVING|WHERE|CREATE|ALTER|DROP)\b',

    # React
    'component':
        r'<[A-Z][A-Za-z0-9_]*',
}


# ============================================================
# COMMENT REMOVAL
# ============================================================

def strip_comments(content, lang):

    if lang in {
        'Python',
        'R',
        'Ruby',
        'Elixir',
        'Elixir Script',
        'Erlang',
        'Erlang Header',
        'Shell',
        'Bash',
        'PowerShell',
    }:

        content = re.sub(
            r'"""[\s\S]*?"""',
            '',
            content
        )

        content = re.sub(
            r"'''[\s\S]*?'''",
            '',
            content
        )

        content = re.sub(
            r'(?m)^\s*#.*$',
            '',
            content
        )

    elif lang in {
        'HTML',
        'Vue',
        'Svelte',
    }:

        content = re.sub(
            r'<!--[\s\S]*?-->',
            '',
            content
        )

        content = re.sub(
            r'/\*[\s\S]*?\*/',
            '',
            content
        )

    elif lang == 'SQL':

        content = re.sub(
            r'--.*',
            '',
            content
        )

        content = re.sub(
            r'/\*[\s\S]*?\*/',
            '',
            content
        )

    else:

        content = re.sub(
            r'/\*[\s\S]*?\*/',
            '',
            content
        )

        content = re.sub(
            r'//.*',
            '',
            content
        )

    return content


# ============================================================
# NESTING
# ============================================================

def calculate_nesting(content):

    depth = 0
    maximum = 0
    cumulative = 0

    pairs = {
        '}': '{',
        ']': '[',
        ')': '(',
    }

    stack = []

    for char in content:

        if char in '{[(':

            stack.append(char)

            depth += 1

            maximum = max(
                maximum,
                depth
            )

        elif char in pairs:

            if stack and stack[-1] == pairs[char]:

                stack.pop()

                depth = max(
                    0,
                    depth - 1
                )

        cumulative += depth

    return maximum, cumulative


# ============================================================
# TOKEN ANALYSIS
# ============================================================

def token_analysis(content):

    tokens = re.findall(
        r'[A-Za-z_][A-Za-z0-9_]*|'
        r'\d+(?:\.\d+)?|'
        r'===|!==|==|!=|<=|>=|&&|\|\||=>|'
        r'\+=|-=|\*=|/=|%=|'
        r'[+\-*/%<>&|^~!?=:]',
        content
    )

    if not tokens:

        return 0, 0

    return (
        len(tokens),
        len(set(tokens))
    )


# ============================================================
# FILE ANALYSIS
# ============================================================

def analyze_file(file_path, lang):

    try:

        with open(
            file_path,
            'r',
            encoding='utf-8',
            errors='ignore'
        ) as f:

            raw = f.read()

    except Exception:

        return None

    physical_lines = len(
        raw.splitlines()
    )

    content = strip_comments(
        raw,
        lang
    )

    lines = [
        line
        for line in content.splitlines()
        if line.strip()
    ]

    code_lines = len(lines)

    if code_lines == 0:
        return None

    # --------------------------------------------------------
    # Pattern counts
    # --------------------------------------------------------

    counts = {}

    for name, pattern in PATTERNS.items():

        try:

            counts[name] = len(
                re.findall(
                    pattern,
                    content,
                    re.IGNORECASE
                )
            )

        except Exception:

            counts[name] = 0

    # Generic call pattern contains function definitions.
    counts['call'] = max(
        0,
        counts['call']
        - counts['function']
    )

    # --------------------------------------------------------
    # Nesting
    # --------------------------------------------------------

    max_nesting, cumulative_nesting = (
        calculate_nesting(content)
    )

    # --------------------------------------------------------
    # Tokens
    # --------------------------------------------------------

    tokens, unique_tokens = (
        token_analysis(content)
    )

    # --------------------------------------------------------
    # Dense lines
    # --------------------------------------------------------

    dense_lines = 0

    very_dense_lines = 0

    for line in lines:

        token_count = len(
            re.findall(
                r'\w+|[^\w\s]',
                line
            )
        )

        if token_count >= 8:
            dense_lines += 1

        if token_count >= 16:
            very_dense_lines += 1

    # ========================================================
    # WEIGHTED COMPLEXITY
    # ========================================================

    structural = (

        counts['branch'] * 8

        + counts['loop'] * 10

        + counts['function'] * 12

        + counts['class'] * 20

        + counts['exception'] * 8

        + counts['boolean'] * 3

        + counts['comparison'] * 3

        + counts['ternary'] * 7

        + counts['optional_chain'] * 3

        + counts['nullish'] * 3

        + counts['arrow'] * 4

        + counts['async'] * 10

        + counts['generator'] * 8

        + counts['chain'] * 3

        + counts['decorator'] * 5

        + counts['generic'] * 5

        + counts['network'] * 10

        + counts['database'] * 12

        + counts['concurrency'] * 20

        + counts['regex'] * 8

        + counts['sql'] * 10

        + counts['component'] * 8

    )

    # --------------------------------------------------------
    # Nesting complexity
    # --------------------------------------------------------

    nesting_score = (

        max_nesting * 20

        + math.sqrt(
            cumulative_nesting
        ) * 5

    )

    # --------------------------------------------------------
    # Information density
    # --------------------------------------------------------

    information_score = (

        tokens * 0.05

        + unique_tokens * 0.1

        + dense_lines * 4

        + very_dense_lines * 8

    )

    # --------------------------------------------------------
    # Complexity density
    # --------------------------------------------------------

    complexity_density = (
        structural / max(code_lines, 1)
    )

    density_score = (

        complexity_density

        * 100

        * math.log2(
            code_lines + 2
        )

    )

    # ========================================================
    # FILE SCORE
    # ========================================================

    score = int(

        # Real code volume
        code_lines * 3

        # Structural complexity
        + structural * 5

        # Nesting
        + nesting_score * 3

        # Information
        + information_score

        # Dense implementation
        + density_score

    )

    return {

        'score': score,

        'physical_lines':
            physical_lines,

        'code_lines':
            code_lines,

        'tokens':
            tokens,

        'unique_tokens':
            unique_tokens,

        'structural':
            structural,

        'max_nesting':
            max_nesting,

        'cumulative_nesting':
            cumulative_nesting,

        'density':
            complexity_density,

        'patterns':
            counts,

    }


# ============================================================
# MAIN DOS SCANNER
# ============================================================

def calculate_dos_score(dos_root):

    if not os.path.isdir(dos_root):

        print(
            f"ERROR: DOS directory "
            f"'{dos_root}' does not exist."
        )

        sys.exit(1)

    totals = Counter()

    languages = Counter()

    files_scanned = 0

    documents = 0

    document_lines = 0

    project_count = 0

    project_names = set()

    file_results = []

    # ========================================================
    # SCAN DOS
    # ========================================================

    for root, dirs, files in os.walk(
        dos_root
    ):

        # Ignore generated/dependency directories
        dirs[:] = [
            d
            for d in dirs
            if d not in SKIP_DIRS
            and not d.startswith('.')
        ]

        for filename in files:

            name_lower = filename.lower()

            extension = os.path.splitext(
                name_lower
            )[1]

            file_path = os.path.join(
                root,
                filename
            )

            # ------------------------------------------------
            # CODE
            # ------------------------------------------------

            if (
                extension in CODE_EXTENSIONS
                or name_lower in SPECIAL_FILES
            ):

                lang = (
                    CODE_EXTENSIONS.get(
                        extension
                    )
                    or SPECIAL_FILES.get(
                        name_lower
                    )
                )

                result = analyze_file(
                    file_path,
                    lang
                )

                if result is None:
                    continue

                files_scanned += 1

                languages[lang] += 1

                # Totals
                for key in [
                    'physical_lines',
                    'code_lines',
                    'tokens',
                    'unique_tokens',
                    'structural',
                    'max_nesting',
                    'cumulative_nesting',
                ]:

                    totals[key] += result[key]

                totals['score'] += result[
                    'score'
                ]

                # Project detection
                relative = os.path.relpath(
                    file_path,
                    dos_root
                )

                parts = relative.split(
                    os.sep
                )

                if (
                    len(parts) >= 2
                    and parts[0] == 'projects'
                ):

                    project_names.add(
                        parts[1]
                    )

                file_results.append(
                    (
                        result['score'],
                        result['code_lines'],
                        file_path
                    )
                )

            # ------------------------------------------------
            # DOCUMENTATION
            # ------------------------------------------------

            elif extension in DOC_EXTENSIONS:

                try:

                    with open(
                        file_path,
                        'r',
                        encoding='utf-8',
                        errors='ignore'
                    ) as f:

                        count = sum(
                            1
                            for line in f
                            if line.strip()
                        )

                    documents += 1

                    document_lines += count

                except Exception:

                    pass

    # ========================================================
    # PROJECT COUNT
    # ========================================================

    project_count = len(
        project_names
    )

    # ========================================================
    # SCALE
    # ========================================================

    code_lines = max(
        totals['code_lines'],
        1
    )

    modules = max(
        files_scanned,
        1
    )

    # ========================================================
    # OVERALL DENSITY
    # ========================================================

    complexity_per_line = (
        totals['structural']
        / code_lines
    )

    # ========================================================
    # SCALE BONUS
    # ========================================================

    scale_bonus = (

        code_lines * 3

        + math.sqrt(
            code_lines
        ) * 100

        + math.log2(
            code_lines + 2
        ) * 100

    )

    # ========================================================
    # ARCHITECTURE BONUS
    # ========================================================

    architecture_bonus = (

        modules * 50

        + project_count * 250

        + math.sqrt(
            modules
        ) * 100

    )

    # ========================================================
    # COMPLEXITY BONUS
    # ========================================================

    complexity_bonus = (

        totals['structural'] * 5

        + totals['max_nesting'] * 50

        + math.sqrt(
            totals['cumulative_nesting']
        ) * 20

    )

    # ========================================================
    # DENSITY BONUS
    # ========================================================

    density_bonus = (

        complexity_per_line

        * 1000

        * math.log2(
            code_lines + 2
        )

    )

    # ========================================================
    # ADVANCED SYSTEM BONUS
    # ========================================================

    advanced_bonus = (

        totals['async'] * 15

        + totals['concurrency'] * 25

        + totals['database'] * 15

        + totals['network'] * 15

        + totals['exception'] * 10

        + totals['generic'] * 8

        + totals['decorator'] * 5

        + totals['regex'] * 10

        + totals['sql'] * 12

        + totals['component'] * 8

        + totals['bitwise'] * 8

    )

    # ========================================================
    # DOCUMENTATION
    # ========================================================

    documentation_bonus = (

        document_lines * 0.5

        + documents * 50

    )

    # ========================================================
    # FINAL SCORE
    # ========================================================

    final_score = int(

        totals['score']

        + scale_bonus

        + architecture_bonus

        + complexity_bonus

        + density_bonus

        + advanced_bonus

        + documentation_bonus

    )

    # ========================================================
    # SORT FILES
    # ========================================================

    file_results.sort(
        reverse=True
    )

    # ========================================================
    # RETURN
    # ========================================================

    return {

        'score':
            final_score,

        'projects':
            project_count,

        'project_names':
            sorted(project_names),

        'files':
            files_scanned,

        'physical_lines':
            totals['physical_lines'],

        'code_lines':
            totals['code_lines'],

        'documents':
            documents,

        'document_lines':
            document_lines,

        'tokens':
            totals['tokens'],

        'unique_tokens':
            totals['unique_tokens'],

        'structural':
            totals['structural'],

        'max_nesting':
            totals['max_nesting'],

        'cumulative_nesting':
            totals['cumulative_nesting'],

        'complexity_per_line':
            complexity_per_line,

        'languages':
            dict(languages),

        'patterns':
            dict(totals),

        'top_files':
            file_results[:10],
    }


# ============================================================
# DISPLAY
# ============================================================

def display_results(result):

    print()
    print("=" * 78)

    print(
        "🧠 DOS — OVERALL ARCHITECTURE SCORE"
    )

    print("=" * 78)

    print()
    print(
        "SCAN SCOPE"
    )

    print("-" * 78)

    print(
        "  DOS ROOT"
    )

    print(
        "  └── projects/"
    )

    print(
        "      └── all recursive source files"
    )

    print()
    print(
        "PROJECT SCALE"
    )

    print("-" * 78)

    print(
        f"  Projects:                 "
        f"{result['projects']:,}"
    )

    print(
        f"  Code modules:             "
        f"{result['files']:,}"
    )

    print(
        f"  Active LOC:               "
        f"{result['code_lines']:,}"
    )

    print(
        f"  Physical LOC:             "
        f"{result['physical_lines']:,}"
    )

    print(
        f"  Documentation files:      "
        f"{result['documents']:,}"
    )

    print(
        f"  Documentation lines:      "
        f"{result['document_lines']:,}"
    )

    print()
    print(
        "COMPUTATIONAL COMPLEXITY"
    )

    print("-" * 78)

    print(
        f"  Structural operations:    "
        f"{result['structural']:,}"
    )

    print(
        f"  Maximum nesting:          "
        f"{result['max_nesting']:,}"
    )

    print(
        f"  Cumulative nesting:       "
        f"{result['cumulative_nesting']:,}"
    )

    print(
        f"  Complexity / LOC:         "
        f"{result['complexity_per_line']:.4f}"
    )

    print()
    print(
        "LANGUAGES"
    )

    print("-" * 78)

    if result['languages']:

        for lang, count in sorted(
            result['languages'].items(),
            key=lambda x: x[1],
            reverse=True
        ):

            print(
                f"  {lang:<28} "
                f"{count:>7} files"
            )

    else:

        print(
            "  No source files detected."
        )

    print()
    print(
        "TOP COMPLEX FILES"
    )

    print("-" * 78)

    for index, (
        score,
        lines,
        path
    ) in enumerate(
        result['top_files'],
        1
    ):

        print(
            f"  {index:>2}. "
            f"{score:>10,} pts  "
            f"{lines:>7,} LOC  "
            f"{path}"
        )

    print()
    print("=" * 78)

    print(
        "🏆 YOUR DOS OVERALL SCORE"
    )

    print()

    print(
        f"              {result['score']:,}"
    )

    print()

    print(
        "The score represents the total "
        "engineering complexity and scale "
        "detected inside DOS."
    )

    print("=" * 78)

    print()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    # --------------------------------------------------------
    # Default:
    #
    #   current directory
    #
    # This assumes you run:
    #
    #   cd ~/DOS
    #   python dos.py
    #
    # --------------------------------------------------------

    target = "."

    if len(sys.argv) > 1:

        target = sys.argv[1]

    result = calculate_dos_score(
        target
    )

    display_results(
        result
    )
