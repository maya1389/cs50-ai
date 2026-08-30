import sys
from operator import itemgetter

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        w, h = draw.textsize(letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        # Loop over variables
        for v in self.domains:
            # Initialise variable to track changes
            changed = False
            # Create copy of domains
            new_set = set(self.domains[v])
            # Loop over domains in v
            for x in self.domains[v]:
                # Check length of variable is same as length of word
                if v.length != len(x):
                    # Make a change to domains if not
                    new_set.remove(x)
                    changed = True
            # Update actual domains
            if changed:
                self.domains[v] = new_set
        return True

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        # Keep track of revisions
        revised = False
        new_set = set(self.domains[x])
        # Loop over x domains
        for w in self.domains[x]:
            # Check if y has 1 word and that matches w
            if w in self.domains[y] and len(self.domains[y]) == 1:
                new_set.remove(w)
                revised = True
                continue
            # Check the overlap works
            if self.crossword.overlaps[x, y] != None:
                pair = self.crossword.overlaps[x, y]
                count = 0
                for u in self.domains[y]:
                    if w[pair[0]] == u[pair[1]]:
                        count += 1
                if count == 0:
                    new_set.remove(w)
                    revised = True
        # Any revisions are added to actual domains
        if revised:
            self.domains[x] = new_set
        return revised

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        # Queue has all the arcs in the csp
        queue = []
        # Either get arcs fro argument in function or from crossword.variables
        if arcs:
            for a in arcs:
                queue.append(a)
        else:
            for a in self.crossword.variables:
                for b in self.crossword.variables:
                    if a != b:
                        queue.append((a, b))
        # Run the following until queue is empty
        while (len(queue) != 0):
            # Pop an arc off the queue
            pair = queue.pop(0)
            # Run revise on it
            if self.revise(pair[0], pair[1]):
                # Check if domain number for x is not 0
                if len(self.domains[pair[0]]) == 0:
                    return False
                # Get all neighbors of x and add arcs to queue (but not pair[1])
                neighbors = self.crossword.neighbors(pair[0])
                for n in neighbors:
                    if n != pair[1]:
                        queue.append((n, pair[0]))
        return True

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        # Know the total number of variables
        total = len(self.crossword.variables)
        # Check if length of assignment is same as total
        if len(assignment) == total:
            return True
        return False

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        # Loop over all assignments
        for v1 in assignment:
            # Check the length of the word
            if len(assignment[v1]) != v1.length:
                return False
            # Loop over assignments again
            for v2 in assignment:
                if v1 != v2:
                    # Check both assignments are not the same
                    if assignment[v1] == assignment[v2]:
                        return False
                    # Check any overlapping
                    if self.crossword.overlaps[v1, v2]:
                        pair = self.crossword.overlaps[v1, v2]
                        if assignment[v1][pair[0]] != assignment[v2][pair[1]]:
                            return False
        
        # Return true if loop completed and not exited with false
        return True

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        # Initialise empty list
        s = []
        # Find all neighboring variables to var
        neighbors = self.crossword.neighbors(var)
        # Loop over all the words in domain[var]
        for w in self.domains[var]:
            # Initialise variable to count number of values effected
            count = 0
            # Loop over neighbors
            for v in neighbors:
                # Check if neighbor is already assigned, ignore if so
                if v in assignment:
                    continue
                # Get overlap indices
                pair = self.crossword.overlaps[var, v]
                # Loop over words in neighbors domain
                for u in self.domains[v]:
                    # Check if word is same, if so add 1 to count
                    if w == u:
                        count += 1
                        # continue with other words
                        continue
                    # If the overlap does not work, a domain value is affected, so add 1 to count
                    if w[pair[0]] != u[pair[1]]:
                        count += 1
            # Append word and count as tuple to the list
            s.append((w, count))
        # Sort the list and return just a sorted list of values
        sorted_s = sorted(s, key=itemgetter(1))
        output = []
        for val in sorted_s:
            output.append(val[0])
        return output

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        # Initialise list to later sort
        unassigned = []
        # Loop over all the variables
        for v in self.crossword.variables:
            # Check if variable is already assigned
            if v in assignment:
                continue
            # Store number of domains
            d = len(self.domains[v])
            # Find the number of neighbors
            neighbors = self.crossword.neighbors(v)
            # Store the number of neighbors
            n = len(neighbors)
            # Update list with all values
            unassigned.append((v, d, n))
        # Check list has elements before sorting
        if len(unassigned) > 0:
            # Sort list, first by domains then by neighbors
            sorted_list = sorted(unassigned, key=itemgetter(1, 2))
            # Return first item in the list
            return sorted_list[0][0]
        
        return None

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        # Check if assignment is complete
        if self.assignment_complete(assignment):
            return assignment
        
        # Choose unassigned variable
        var = self.select_unassigned_variable(assignment)
        # Order the domain values
        values = self.order_domain_values(var, assignment)
        # Loop over the domains values
        for v in values:
            # Copy the assignment
            new_assignment = assignment.copy()
            # Add a key value pair to the new assignment
            new_assignment[var] = v
            # Check this is consistent
            if self.consistent(new_assignment):
                # Maintain arc consistency
                arcs = []
                neighbors = self.crossword.neighbors(var)
                for n in neighbors:
                    arcs.append((n, var))
                if self.ac3(arcs):
                    # Add inferences to new assignment
                    for v in self.domains:
                        if len(self.domains[v]) == 1 and v not in new_assignment:
                            for i in self.domains[v]:
                                new_assignment[v] = i
                # Recursively call backtrack
                result = self.backtrack(new_assignment)
                # Check if result is not None
                if result is not None:
                    return result
        return None


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
