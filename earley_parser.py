class Rule:
    def __init__(self, left, right, dot_position, start_pos):
        self.left = left
        self.right = right
        self.dot_position = dot_position
        self.start_pos = start_pos
    
    def __eq__(self, other):
        return (self.left == other.left and 
                self.right == other.right and 
                self.dot_position == other.dot_position and 
                self.start_pos == other.start_pos)
    
    def __hash__(self):
        return hash((self.left, self.right, self.dot_position, self.start_pos))
    
    def __str__(self):
        right_part = list(self.right)
        right_part.insert(self.dot_position, "•")
        return f"[{self.left} → {' '.join(right_part)}, {self.start_pos}]"

    def is_complete(self):
        # check for dot in the end
        return self.dot_position >= len(self.right)

    def next_symbol(self):
        # next symbol after dot
        if self.is_complete():
            return None
        return self.right[self.dot_position]

    def advance_dot(self):
        # new rule with moved dot
        return Rule(self.left, self.right, self.dot_position + 1, self.start_pos)

class EarleyParser:
    def __init__(self, grammar):
        # grammar: {nonterminal: [right rules list of tuples]}
        self.grammar = grammar
        # set of rules(structures) for each situation
        self.chart = []
        
    def predict(self, state, position):
        next_sym = state.next_symbol()
        if next_sym in self.grammar:
            new_states = [Rule(next_sym, rhs, 0, position) 
                         for rhs in self.grammar[next_sym]]
            for new_state in new_states:
                self.chart[position].add(new_state)

    def scan(self, state, position, input_string):
        if position < len(input_string):
            next_sym = state.next_symbol()
            if next_sym == input_string[position]:
                self.chart[position + 1].add(state.advance_dot())

    def complete(self, state, position):
        if state.is_complete():
            for s in list(self.chart[state.start_pos]):
                if not s.is_complete() and s.next_symbol() == state.left:
                    self.chart[position].add(s.advance_dot())

    def parse(self, input_string, start_symbol):
        """
        Разбирает входную строку согласно грамматике, печатает ситуации
        True, если строка принадлежит языку
        """
        self.chart = [set() for _ in range(len(input_string) + 1)]
        
        # grammar expansion
        initial_rule = Rule('S1', (start_symbol,), 0, 0)
        self.chart[0].add(initial_rule)
        
        # iterationg through situations
        for i in range(len(input_string) + 1):
            while True:
                chart_size = len(self.chart[i])
                for state in list(self.chart[i]):
                    if not state.is_complete():
                        next_sym = state.next_symbol()
                        if next_sym in self.grammar:
                            self.predict(state, i)
                        else:
                            self.scan(state, i, input_string)
                    else:
                        self.complete(state, i)
                
                if len(self.chart[i]) == chart_size:
                    break
            
            # printing situations
            if len(self.chart[i]) == 0 and len(self.chart[i-1]) != 0:
                print(f"\nСитуация {i}")
                print(f"{input_string[:i]} • {input_string[i:]}")
                print("Empty")
            elif len(self.chart[i]) == 0 and len(self.chart[i-1]) == 0:
                break
            else:
                print(f"\nСитуация {i}")
                if i == 0:
                    print(f"• {input_string}")
                else:
                    print(f"{input_string[:i]} • {input_string[i:]}")
                for state in self.chart[i]:
                # for state in sorted(self.chart[i], key=lambda x: (x.left, x.right, x.dot_position, x.start_pos)):
                    # rules(structures) print
                    right_part = list(state.right)
                    right_part.insert(state.dot_position, "•")
                    rule_str = f"[{state.left} → {' '.join(right_part)}, {state.start_pos}]"
                    print(rule_str)

        # word check
        for state in self.chart[len(input_string)]:
            if (state.left == 'S1' and 
                state.is_complete() and 
                state.start_pos == 0):
                return True
        return False


def input_grammar():
    grammar = {}
    print("Формат: НЕТЕРМИНАЛ -> ПРАВАЯ_ЧАСТЬ")
    print("Используйте пробел для разделения символов в правой части (Пример: S -> A + S).")
    print("Для завершения ввода правил введите пустую строку.")
    print("Вывод структур ситуации произвольный, т.к. используется set. На алгоритм не влияет.")
    print("Введите правила: ")
    
    while True:
        rule_input = input().strip()
        if not rule_input:
            break
        
        try:
            left, right = rule_input.split('->')
            left = left.strip()
            right = right.strip().split()

            if left not in grammar:
                grammar[left] = []
            grammar[left].append(tuple(right))
        except ValueError:
            print("Ошибка ввода. Используйте формат: НЕТЕРМИНАЛ -> ПРАВАЯ_ЧАСТЬ")
    
    return grammar

def main():
    grammar = input_grammar()
    
    start_symbol = list(grammar.keys())[0]
    print(f"Начальный символ грамматики: {start_symbol}")
    
    parser = EarleyParser(grammar)
    
    while True:
        word = input("\nВведите слово ('exit' для выхода): ").strip().replace(' ', '')
        if word.lower() == 'exit':
            break
        try:
            result = parser.parse(word, start_symbol)
            print('\n' + str(result))
        except Exception as e:
            print(f"Ошибка: {e}")

# def main():
#     # S -> A + S
#     # S -> b
#     # A -> S - A
#     # A -> a
#     grammar = {
#         'S':[('A', '+', 'S'), ('b',)],
#         'A':[('S', '-', 'A'), ('a',)]
#     }

#     parser = EarleyParser(grammar)
#     test_strings = ['a - b', 'a + b', 'c-g']

#     for s in test_strings:
#         result = parser.parse(s.strip().replace(' ',''), 'S')
#         print('\n'+str(result))

if __name__ == "__main__":
    main()