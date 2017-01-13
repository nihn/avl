from collections import deque
from operator import lt
from random import randrange


class NullNode(object):
    height = -1
    value = None

    def __repr__(self):
        return "<{}>".format(self.__class__.__name__)

    def __bool__(self):
        return False

    def __setattr__(self, key, value):
        pass


class Node(object):
    def __init__(self, value, left=None, right=None, parent=None):
        self.height = 0
        self.value = value
        self.left = left or NullNode()
        self.right = right or NullNode()
        self.parent = parent
        self.count = 1

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return "<{}: {}, h: {}, b: {}>".format(
            self.__class__.__name__, self.value,
            self.height, self.balance)

    def __iter__(self):
        yield self
        if self.left:
            yield from self.left
        if self.right:
            yield from self.right

    def __getitem__(self, item):
        try:
            return getattr(self, item)
        except AttributeError as e:
            raise KeyError('%s not found' % item) from e

    def __setitem__(self, key, value):
        if key not in self.__dict__:
            raise KeyError('Cannot set key %s' % key)
        setattr(self, key, value)

    def details(self):
        return "<{}: {}, h: {}, b: {}, c: {}, l: {}, r: {}, p: {}>".format(
            self.__class__.__name__, self.value,
            self.height, self.balance, self.count,
            repr(self.left), repr(self.right), repr(self.parent))

    def iter_left(self):
        yield self
        if self.left:
            yield from self.left.iter_left()

    def iter_right(self):
        yield self
        if self.right:
            yield from self.right.iter_right()

    def update_height(self):
        self.height = max(self.left.height, self.right.height) + 1

    @property
    def balance(self):
        return self.right.height - self.left.height


class AVL(object):
    def __init__(self, values):
        self.root = Node(values[0])
        self.max_value_len = len(str(self.root))
        self.max_repr_len = len(repr(self.root))

        for value in values[1:]:
            self.insert(value)

    def __call__(self):
        return self.root

    def insert(self, value):
        """
        Insert node into Tree, do needed rotations to preserve AVL properties.
        :param value: value to be inserted.
        """
        self.max_value_len = max(self.max_value_len, len(str(value)))
        self.max_repr_len = max(self.max_repr_len, len(repr(value)))
        self._insert(self.root, value)

    def delete(self, value, all=False):
        """
        Delete value from Tree, do needed rotations to preserve AVL properties.
        :param value: value to be deleted.
        :param all: if True all matched values will be deleted.
        """
        self._delete(self.root, value, all)

    def __iter__(self):
        return iter(self.root)

    def _get_structure_string(self, format):
        """
        Get text Tree representation, string is printed from left to right
        where most right node is the tree's root.
        :param format: one on 'r' or 's'. 'r' is for more detailed information
        about nodes in the tree.
        :return: string representing Tree structure
        """
        if format not in ['r', 's']:
            raise TypeError('format arg must be one of "s" or "r"')

        string = []
        max_len = self.max_value_len if format == 's' else self.max_repr_len

        def _get(node, index):
            string.append(('{!%s:^%s}' % (format, max_len)).format(node))

            if node.left:
                string.append(' - ')
                _get(node.left, index + 1)

            if node.right:
                string.append('\n{0}\\\n{0} - '.format(
                    (index * (max_len + 3) + max_len) * ' '))
                _get(node.right, index + 1)

        _get(self.root, 0)
        return ''.join(string)

    def __str__(self):
        return self._get_structure_string('s')

    def __repr__(self):
        return self._get_structure_string('r')

    def _update_parent_leaf(self, node, new_node):
        """
        Update Node's parent left or right pointer to point to new_node. If
        Node has no parent, set new_node as root.
        :param node: old child
        :param new_node: new child
        """
        if node.parent:
            if node.parent.left == node:
                node.parent.left = new_node
            else:
                node.parent.right = new_node
        else:
            self.root = new_node

    def _insert(self, node, value):
        h = 0

        if value == node.value:
            node.count += 1
        elif value < node.value and node.right:
            h = self._insert(node.right, value)
        elif value > node.value and node.left:
            h = self._insert(node.left, value)
        else:
            new_node = Node(value, parent=node)
            side = 'left' if value > node.value else 'right'

            if node[side]:
                node[side].parent = new_node
                new_node.height = node[side].height + 1

            node[side] = new_node

        node.height = max(node.height, h + 1)
        self.rotate(node)

        return node.height

    def _do_delete(self, node):
        """
        Do actual delete, replace node with it's children or NullNode
        :param node: node to be deleted
        """
        if node.left and not node.right:
            new_node = node.left
        elif node.right and not node.left:
            new_node = node.right
        else:
            new_node = NullNode()

        if new_node:
            new_node.update_height()
            new_node.parent = node.parent

        self._update_parent_leaf(node, new_node)

    def _delete(self, node, value, all):
        compare_fun = lt

        if node.value is None:
            raise ValueError('Value %s not found' % value)

        if node.value == value:
            if not all and node.count > 1:
                node.count -= 1
                return
            elif not node.left or not node.right:
                self._do_delete(node)
                return

            node_to_switch = deque(
                node.right.iter_left() if node.right.height > node.left.height
                else node.left.iter_right(), maxlen=1).pop()

            node.value, node_to_switch.value = node_to_switch.value, node.value
            compare_fun = lambda a, b: not lt(a, b)

        if compare_fun(value, node.value):
            self._delete(node.right, value, all)
        else:
            self._delete(node.left, value, all)

        node.update_height()
        self.rotate(node)

    def _rotate(self, node, left):
        """
        Rotate subtree to preserve correct balance in the AVL Tree.
        :param node: node on which subtree will be rotated
        :param left: if True this will be left-rotation
        """
        sides = ['left', 'right']
        side, o_side = sides if left else reversed(sides)

        x = node
        y = node[side]

        self._update_parent_leaf(x, y)

        if y[side].height == y[o_side].height:
            x.height = y.height
            y.height += 1
        else:
            x.height = y.height - 1

        x[side] = y[o_side]
        x[side].parent = x
        y[o_side] = x
        y.parent = x.parent
        x.parent = y

    def _rotate_left(self, node):
        self._rotate(node, True)

    def _rotate_right(self, node):
        self._rotate(node, False)

    def rotate(self, node):
        """
        Check if rotation is needed for the subtree with node as root
        and if so do the correct one.
        :param node: root of the subtree which would be rotated
        """
        if abs(node.balance) < 2:
            return

        if node.balance < -1 and node.left.balance < 0:
            self._rotate_left(node)
        elif node.balance > 1 and node.right.balance > 0:
            self._rotate_right(node)
        elif node.balance < -1 and node.left.balance > 0:
            self._rotate_right(node.left)
            self._rotate_left(node)
        elif node.balance > 1 and node.right.balance < 0:
            self._rotate_left(node.right)
            self._rotate_right(node)


lst = [41, 20, 65, 29, 50, 11, 26, 23, 55]
lst1 = [4, 64, 8, 95, 68, 80, 75, 14, 10]
lst2 = [randrange(100) for i in range(50)]
avl = AVL(lst)
print(avl, '\n', '*' * 100)
avl.delete(41)
avl.delete(55)
avl.delete(20)
avl.delete(29)

print(repr(avl), '\n', '*' * 100)
avl1 = AVL(lst1)
print(avl1, '\n', '*' * 100)
avl2 = AVL(lst2)
print(avl2)
