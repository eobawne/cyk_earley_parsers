class Symbol:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value
    
    def __eq__(self, other):
        if not isinstance(other, Symbol):
            return False
        return self.value == other.value
    
    def __hash__(self):
        return hash(self.value)

class Terminal(Symbol):
    pass

class Epsilon(Symbol):
    def __init__(self):
        super().__init__('ε')

class Nonterminal(Symbol):
    def __init__(self, value):
        if not value[0].isupper():
            raise ValueError("Nonterminal must start with uppercase letter")
        if len(value) > 3:
            raise ValueError("Nonterminal can't be longer than 3 characters")
        super().__init__(value)

class GrammarRule:
    def __init__(self, lhs, rhs, rule_number=None):
        self.lhs = lhs
        self.rhs = rhs
        self.rule_number = rule_number

    def __str__(self):
        rule_num_str = f"{self.rule_number}. " if self.rule_number is not None else ""
        if not self.rhs:  # Empty RHS (epsilon)
            return f"{rule_num_str}{self.lhs} -> ε"
        return f"{rule_num_str}{self.lhs} -> {' '.join(str(symbol) for symbol in self.rhs)}"
    def __eq__(self, other):
        if not isinstance(other, GrammarRule):
            return False
        return (self.lhs == other.lhs and 
                len(self.rhs) == len(other.rhs) and 
                all(s1 == s2 for s1, s2 in zip(self.rhs, other.rhs)))
    def __hash__(self):
        return hash((self.lhs, tuple(self.rhs)))

class Grammar:
    def __init__(self):
        self.rules = set()
        self._next_rule_number = 1

    def add_rule(self, rule_str, position=None):
        parts = rule_str.split("->")
        if len(parts) != 2:
            raise ValueError("Invalid rule format")

        lhs_str = parts[0].strip()
        rhs_str = parts[1].strip()

        lhs = Nonterminal(lhs_str)

        # epsilon cases
        if rhs_str == "" or rhs_str.isspace() or rhs_str == "eps" or rhs_str == "ε":
            rhs = []  # empty list == epsilon rhs
        else:
            rhs = []
            i = 0
            # no spaces allowed
            rhs_str = rhs_str.replace(" ", "")
            while i < len(rhs_str):
                if rhs_str[i].isupper():
                    # nonterminal (nt)
                    current_nt = rhs_str[i]
                    i += 1
                    # nt chars (number or prime)
                    if i < len(rhs_str):
                        next_char = rhs_str[i]
                        if next_char.isdigit() or next_char == "'":
                            current_nt += next_char
                            i += 1
                    rhs.append(Nonterminal(current_nt))
                else:
                    # terminal (t)
                    if rhs_str[i] == "'":
                        # if ' is a part of previous nt
                        if rhs and isinstance(rhs[-1], Nonterminal):
                            rhs[-1] = Nonterminal(rhs[-1].value + "'")
                        else:
                            rhs.append(Terminal(rhs_str[i]))
                    else:
                        rhs.append(Terminal(rhs_str[i]))
                    i += 1

        new_rule = GrammarRule(lhs, rhs)
        if new_rule in self.rules:
            return
        if position is None:
            new_rule.rule_number = self._next_rule_number
            self._next_rule_number += 1
            self.rules.add(new_rule)
        else:
            if position < 1:
                raise ValueError("Rule position must be 1 or greater")
            
            insert_index = position - 1
            for rule in self.rules[insert_index:]:
                if rule.rule_number:
                    rule.rule_number += 1
            
            new_rule.rule_number = position
            self.rules.add(new_rule)
            self._next_rule_number = max(self._next_rule_number, len(self.rules) + 1)

    def print_rules(self):
        print("\n".join(str(rule) for rule in self.get_rules_list()))

    def __getitem__(self, index):
        return self.get_rules_list()[index]

    def get_rules_list(self):
        return sorted(list(self.rules), key=lambda x: x.rule_number if x.rule_number else float('inf'))

    def __iter__(self):
        return iter(self.get_rules_list())

    def __len__(self):
        return len(self.rules)

def remove_nonproductive(grammar):
    def find_productive_nonterminals():
        productive = set()
        changed = True
        
        while changed:
            changed = False
            for rule in grammar:
                # skip if LHS is known to be productive
                if rule.lhs.value in productive:
                    continue
                
                # check if all symbols in RHS are either t or productive nt
                all_productive = True
                for symbol in rule.rhs:
                    if isinstance(symbol, Nonterminal):
                        if symbol.value not in productive:
                            all_productive = False
                            break
                    # Terminals are always productive
                
                # if all RHS symbols productive, add LHS to productive set
                if all_productive:
                    productive.add(rule.lhs.value)
                    changed = True
                    
        return productive
    
    productive_nts = find_productive_nonterminals()
    
    # grammar with rules that contains productive nt
    new_grammar = Grammar()
    
    # rules where:
    # 1. LHS is productive
    # 2. ALL nonterminals in RHS are productive
    for rule in grammar:
        if rule.lhs.value in productive_nts:
            all_rhs_productive = True
            for symbol in rule.rhs:
                if isinstance(symbol, Nonterminal):
                    if symbol.value not in productive_nts:
                        all_rhs_productive = False
                        break
            
            if all_rhs_productive:
                rule_str = f"{rule.lhs.value} -> {''.join(symbol.value for symbol in rule.rhs)}"
                new_grammar.add_rule(rule_str)
    
    return new_grammar

def remove_unreachable(grammar, start_symbol='S'):
    # set of reachable nonterminals with start symbol
    reachable = {Nonterminal(start_symbol)}
    
    # sizes to detect when no new nt are added
    old_size = 0
    new_size = 1
    
    # while still finding new reachable nt
    while old_size != new_size:
        old_size = len(reachable)
        
        for rule in grammar:
            if rule.lhs in reachable:
                # add all nonterminals from RHS
                for symbol in rule.rhs:
                    if isinstance(symbol, Nonterminal):
                        reachable.add(symbol)
        
        new_size = len(reachable)
    
    # grammar with only reachable productions
    new_grammar = Grammar()
    # rules where LHS is reachable
    for rule in grammar:
        if rule.lhs in reachable:
            rhs_str = ''.join(symbol.value for symbol in rule.rhs)
            rule_str = f"{rule.lhs.value}->{rhs_str}"
            new_grammar.add_rule(rule_str)
    
    return new_grammar

def remove_epsilon_rules(grammar, start_symbol):
    # find direct epsilon producers (inappropriate movie joke)
    eps_producers = set()
    for rule in grammar:
        # empty RHS = epsilon
        if not rule.rhs:
            eps_producers.add(rule.lhs)
    
    # find indirect epsilon producers
    changed = True
    while changed:
        changed = False
        for rule in grammar:
            if rule.lhs not in eps_producers:
                # check if all symbols in RHS are in eps_producers
                if rule.rhs and all(symbol in eps_producers for symbol in rule.rhs):
                    eps_producers.add(rule.lhs)
                    changed = True
    
    new_grammar = Grammar()
    
    # if start symbol in eps_producers
    if start_symbol in eps_producers:
        new_start = Nonterminal(start_symbol.value + "1")
        new_grammar.add_rule(f"{new_start} -> {start_symbol}")
        new_grammar.add_rule(f"{new_start} -> ε")
        start_symbol = new_start
    
    for rule in grammar:
        # skip epsilon rules
        if not rule.rhs:
            continue
            
        # find positions of eps-producers in RHS
        eps_positions = []
        for i, symbol in enumerate(rule.rhs):
            if symbol in eps_producers:
                eps_positions.append(i)
                
        if not eps_positions:
            # if no eps-producers in RHS, keep the rule as is
            new_grammar.add_rule(f"{rule.lhs} -> {''.join(str(s) for s in rule.rhs)}")
            continue
            
        # generate all combinations using binary masks
        n_eps = len(eps_positions)
        for mask in range(2**n_eps):
            new_rhs = []
            skip_positions = set()
            
            # convert mask to binary and determine which eps-producers to skip
            for i in range(n_eps):
                if not (mask & (1 << i)):
                    skip_positions.add(eps_positions[i])
                    
            # new RHS with Mask
            for i, symbol in enumerate(rule.rhs):
                if i not in skip_positions:
                    new_rhs.append(symbol)
                    
            # add rule if RHS not empty
            if new_rhs:
                new_grammar.add_rule(f"{rule.lhs} -> {''.join(str(s) for s in new_rhs)}")
    
    # new_grammar.rules = sorted(list(set(new_grammar.rules)), key=lambda x: x.rule_number if x.rule_number else float('inf'))

    return new_grammar

def eliminate_chain_rules(grammar):
    new_grammar = Grammar()
    
    # function to find CHAIN(A) for a nonterminal A
    def find_chain(nt, visited=None):
        if visited is None:
            visited = set()
        
        if nt in visited:
            return set()
            
        chain = {nt}
        visited.add(nt)
        
        # find all direct chain rules for this nt
        for rule in grammar.rules:
            if rule.lhs == nt and len(rule.rhs) == 1 and isinstance(rule.rhs[0], Nonterminal):
                chain.update(find_chain(rule.rhs[0], visited))
                
        return chain

    processed_rules = set()
    for rule in grammar.rules:
        nt = rule.lhs
        chain = find_chain(nt)
        
        # for each nt in the chain
        for b in chain:
            # look for non-chain rules with B(any nt) on the left side
            for rule_b in grammar.rules:
                if rule_b.lhs == b:
                    # skip chain rules
                    if len(rule_b.rhs) == 1 and isinstance(rule_b.rhs[0], Nonterminal):
                        continue
                        
                    # new rule: A -> γ where B -> γ is a non-chain rule
                    new_rule_str = f"{nt} -> {''.join(str(symbol) for symbol in rule_b.rhs)}"
                    
                    # add only if not already processed
                    if new_rule_str not in processed_rules:
                        new_grammar.add_rule(new_rule_str)
                        processed_rules.add(new_rule_str)

    return new_grammar

def to_chomsky_normal_form(grammar):
    cnf = Grammar()
    new_rules = {}
    terminal_rules = {}
    next_nt_number = 1

    def get_new_nonterminal():
        nonlocal next_nt_number
        while True:
            new_nt = f"X{next_nt_number}"
            next_nt_number += 1
            # check if the nt already in use
            if not any(rule.lhs.value == new_nt for rule in grammar.rules):
                return Nonterminal(new_nt)

    # handle t within longer rules
    for rule in grammar:
        if len(rule.rhs) >= 2:
            new_rhs = []
            for symbol in rule.rhs:
                if isinstance(symbol, Terminal):
                    if symbol.value not in terminal_rules:
                        new_nt = get_new_nonterminal()
                        terminal_rules[symbol.value] = new_nt
                        # new rule for t
                        cnf.add_rule(f"{new_nt.value} -> {symbol.value}")
                    new_rhs.append(terminal_rules[symbol.value])
                else:
                    new_rhs.append(symbol)
            new_rules[rule] = (rule.lhs, new_rhs)
        else:
            # keep single-symbol rules as they are
            new_rule = GrammarRule(rule.lhs, rule.rhs)
            cnf.rules.add(new_rule)

    # break down rules with more than 2 nt
    for original_rule, (lhs, rhs) in new_rules.items():
        current_rhs = rhs.copy()
        
        while len(current_rhs) > 2:
            new_nt = get_new_nonterminal()
            # create new rule for last two symbols
            new_rule = GrammarRule(
                new_nt,
                [current_rhs[-2], current_rhs[-1]]
            )
            cnf.rules.add(new_rule)
            # replace last two symbols with new nt
            current_rhs = current_rhs[:-2] + [new_nt]
        
        if current_rhs: # add final rule
            final_rule = GrammarRule(lhs, current_rhs)
            cnf.rules.add(final_rule)

    # reassign rule numbers
    sorted_rules = sorted(cnf.rules, key=lambda x: x.rule_number if x.rule_number else float('inf'))
    for i, rule in enumerate(sorted_rules, 1):
        rule.rule_number = i
    cnf._next_rule_number = len(cnf.rules) + 1

    return cnf

class CYKParser:
    def __init__(self, grammar):
        # get start symbol from first rule
        self.start_symbol = grammar[0].lhs if grammar else None
        
        # remove unproductive, unreachable, epsilon, chain rules and transform to our dearly beloved cnf
        if self.start_symbol:
            grammar = remove_nonproductive(grammar)
            grammar = remove_unreachable(grammar, self.start_symbol.value)
            grammar = remove_epsilon_rules(grammar, self.start_symbol)
            grammar = eliminate_chain_rules(grammar)
            self.grammar = to_chomsky_normal_form(grammar)
        else:
            self.grammar = grammar
        self.recognition_table = {}
        
    def parse(self, word):
        n = len(word)
        self.recognition_table = {}
        
        # j = 1
        for i in range(n):
            for rule in self.grammar:
                if len(rule.rhs) == 1 and isinstance(rule.rhs[0], Terminal) and rule.rhs[0].value == word[i]:
                    self.add_to_table(i, 1, (rule.lhs, rule.rule_number))
        
        # fill table (j > 1)
        for j in range(2, n + 1):
            for i in range(n - j + 1):
                for k in range(1, j):
                    for rule in self.grammar:
                        if len(rule.rhs) == 2:
                            if (i, k) in self.recognition_table and \
                            (i + k, j - k) in self.recognition_table:
                                for left_nt, _ in self.recognition_table[(i, k)]:
                                    for right_nt, _ in self.recognition_table[(i + k, j - k)]:
                                        if rule.rhs[0] == left_nt and rule.rhs[1] == right_nt:
                                            self.add_to_table(i, j, (rule.lhs, rule.rule_number))
        
        # total recall
        if (0, n) in self.recognition_table and self.start_symbol:
            for nt, _ in self.recognition_table[(0, n)]:
                if nt == self.start_symbol:
                    rule_numbers = self.get_derivation_rules(word)
                    return True, rule_numbers
        return False, None

    def add_to_table(self, i, j, nt_rule):
        if (i, j) not in self.recognition_table:
            self.recognition_table[(i, j)] = set()
        self.recognition_table[(i, j)].add(nt_rule)
            
    def get_derivation_rules(self, word):
        n = len(word)
        if not (0, n) in self.recognition_table or not self.start_symbol:
            return []
        
        # find the final rule in parsing (start symbol in pos (0, len(word))
        start_rule_number = None
        for nt, rule_number in self.recognition_table[(0, n)]:
            if nt == self.start_symbol:
                start_rule_number = rule_number
                break
        if not start_rule_number:
            return []
        
        def _trace_rules(i, j, current_nt):
            if j == 1:
                for rule in self.grammar:
                    if len(rule.rhs) == 1 and isinstance(rule.rhs[0], Terminal) and rule.lhs == current_nt and rule.rhs[0].value == word[i]:
                        return [rule.rule_number]
                return []
            
            for k in range(1, j):
                if (i, k) in self.recognition_table and (i + k, j - k) in self.recognition_table:
                    for left_nt, left_rule_number in self.recognition_table[(i, k)]:
                        for right_nt, right_rule_number in self.recognition_table[(i + k, j - k)]:
                            for rule in self.grammar:
                                if rule.lhs == current_nt and len(rule.rhs) == 2 and rule.rhs[0] == left_nt and rule.rhs[1] == right_nt:
                                    return [rule.rule_number] + _trace_rules(i, k, left_nt) + _trace_rules(i + k, j - k, right_nt)
            return []
        
        return _trace_rules(0, n, self.start_symbol)
        # return [start_rule_number] + _trace_rules(0, n, self.start_symbol)

    def print_table(self, word):
        n = len(word)

        # figuring out max width for each column
        # +1 for the row labels
        column_widths = [0] * (n + 1)
        
        # first column
        max_width = max(len(f"i={i+1}, {word[i]}") for i in range(n))
        column_widths[0] = max(column_widths[0], max_width)
        # header row
        for j in range(1, n + 1):
            max_width = len(f"j={j}")
            column_widths[j] = max(column_widths[j], max_width)

        for i in range(n):
            for j in range(1, n + 1):
                cell_values = []
                if (i, j) in self.recognition_table:
                    cell_values = [f"{nt.value}, {rule_num}" for nt, rule_num in self.recognition_table[(i, j)]]
                max_width = len(' ; '.join(cell_values))
                column_widths[j] = max(column_widths[j], max_width)

        # header and separator
        # top left corner padding
        header = ["| " + " ".ljust(column_widths[0]) + " |"]
        separator = ["| "+"---".ljust(column_widths[0], "-") + " |"]
        for j in range(1, n+1):
            header.append(f" {('j=' + str(j)).center(column_widths[j])} |")
            separator.append(" " + "---".ljust(column_widths[j], "-") + " |")
        print("".join(header))
        print("".join(separator))
        
        for i in range(n):
            row = [f"| {f'i={i+1}, {word[i]}'.ljust(column_widths[0])} |"]
            for j in range(1, n + 1):
                cell_values = []
                if (i, j) in self.recognition_table:
                    cell_values = [f"{nt.value}, {rule_num}" for nt, rule_num in self.recognition_table[(i, j)]]
                row.append(f" {(' ; '.join(cell_values)).center(column_widths[j])} |")
            print("".join(row))

def main():
    grammar = Grammar()

    print(''.join("===" for i in range(32)))
    print("Формат правил: НЕТЕРМИНАЛ -> ПРАВАЯ_ЧАСТЬ")
    print("Используйте пробел для разделения символов в правой части (Пример: S -> A + S).")
    print("ВНИМАНИЕ: Порядок вывода и нумерации правил не будет сохраняться после преобразования в НФХ!")
    print("До перевода в НФХ, во входной грамматике производится удаление:\n 1. непроизводящих символов,\n 2. недостижимых символов,\n 3. ε-правил,\n 4. цепных правил.")
    print("Правила с начальным символом грамматики так же могут быть не первыми по нумерации!")
    print(''.join("===" for i in range(32)))
    print("Введите правила грамматики (или пустую строку для завершения):")
    while True:
        rule_str = input()
        if rule_str.strip() == '':
            break
        try:
            grammar.add_rule(rule_str)
        except ValueError as e:
            print(f"Ошибка: {e}")
    
    # grammar.add_rule("S -> S + A")
    # grammar.add_rule("S -> S - A")
    # grammar.add_rule("S -> A")
    # grammar.add_rule("A -> a")
    # grammar.add_rule("A -> b")

    # grammar.add_rule("S -> A + S")
    # grammar.add_rule("S -> A - S")
    # grammar.add_rule("S -> A")
    # grammar.add_rule("A -> a")
    # grammar.add_rule("A -> b")

    if not grammar.rules:
        print("Вы не ввели ни одного правила. До свидания")
        return
    
    print("Входная грамматика: ")
    grammar.print_rules()
    
    parser = CYKParser(grammar)
    print("\nГрамматика в НФХ: ")
    parser.grammar.print_rules()

    while True:
        word = input("Введите слово для проверки (или пустую строку для выхода): ")
        if word.strip() == '':
            break
            
        accepted, derivation_rules = parser.parse(word)
            
        parser.print_table(word)
        
        if accepted:
            print(f"TRUE: {','.join(str(rule_number) for rule_number in derivation_rules)}")
        else:
            print("FALSE")

if __name__ == "__main__":
    main()