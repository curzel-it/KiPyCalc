"""Dirac notation for states."""


from sympy import Expr, Symbol, Function, integrate, Expr
from sympy import Lambda, oo, conjugate, Tuple, sqrt, cacheit
from sympy.printing.pretty.stringpict import prettyForm
from sympy.physics.quantum.operator import Operator

from sympy.physics.quantum.qexpr import (
    QExpr, dispatch_method
)

__all__ = [
    'KetBase',
    'BraBase',
    'StateBase',
    'State',
    'Ket',
    'Bra',
    'TimeDepState',
    'TimeDepBra',
    'TimeDepKet',
    'Wavefunction'
]


#-----------------------------------------------------------------------------
# States, bras and kets.
#-----------------------------------------------------------------------------

# LIGHT VERTICAL BAR
_straight_bracket = u"\u2758"

# MATHEMATICAL LEFT ANGLE BRACKET
_lbracket = u"\u27E8"
_rbracket = u"\u27E9"

# Other options for unicode printing of <, > and | for Dirac notation.

# VERTICAL LINE
# _straight_bracket = u"\u007C"

# LEFT-POINTING ANGLE BRACKET
# _lbracket = u"\u2329"
# _rbracket = u"\u232A"

# LEFT ANGLE BRACKET
# _lbracket = u"\u3008"
# _rbracket = u"\u3009"


class StateBase(QExpr):
    """Abstract base class for general abstract states in quantum mechanics.

    All other state classes defined will need to inherit from this class. It
    carries the basic structure for all other states such as dual, _eval_dagger
    and label.

    This is an abstract base class and you should not instantiate it directly,
    instead use State.
    """

    @classmethod
    def _operators_to_state(self, ops, **options):
        """ Returns the eigenstate instance for the passed operators.

        This method should be overridden in subclasses. It will handle
        being passed either an Operator instance or set of Operator
        instances. It should return the corresponding state INSTANCE
        or simply raise a NotImplementedError. See cartesian.py for an
        example.
        """

        raise NotImplementedError("Cannot map operators to states in this class. Method not implemented!")

    def _state_to_operators(self, op_classes, **options):
        """ Returns the operators which this state instance is an
        eigenstate of.

        This method should be overridden in subclasses. It will be
        called on state instances and be passed the operator classes
        that we wish to make into instances. The state instance will
        then transform the classes appropriately, or raise a
        NotImplementedError if it cannot return operator
        instances. See cartesian.py for examples,
        """

        raise NotImplementedError("Cannot map this state to operators. Method not implemented!")

    @property
    def operators(self):
        """Return the operator(s) that this state is an eigenstate of"""
        from operatorset import state_to_operators #import internally to avoid circular import errors
        return state_to_operators(self)

    def _enumerate_state(self, num_states, **options):
        raise NotImplementedError("Cannot enumerate this state!")

    def _represent_default_basis(self, **options):
        return self._represent(basis=self.operators)

    #-------------------------------------------------------------------------
    # Dagger/dual
    #-------------------------------------------------------------------------

    @property
    def dual(self):
        """Return the dual state of this one."""
        return self.dual_class()._new_rawargs(self.hilbert_space, *self.args)

    @classmethod
    def dual_class(self):
        """Return the class used to construt the dual."""
        raise NotImplementedError(
            'dual_class must be implemented in a subclass'
        )

    def _eval_dagger(self):
        """Compute the dagger of this state using the dual."""
        return self.dual

    #-------------------------------------------------------------------------
    # Printing
    #-------------------------------------------------------------------------

    def _print_contents(self, printer, *args):
        label = self._print_label(printer, *args)
        return '%s%s%s' % (self.lbracket, label, self.rbracket)

    def _print_contents_pretty(self, printer, *args):
        from sympy.printing.pretty.stringpict import prettyForm
        pform = self._print_label_pretty(printer, *args)
        pform = prettyForm(*pform.left((self.lbracket_pretty)))
        pform = prettyForm(*pform.right((self.rbracket_pretty)))
        return pform

    def _print_contents_latex(self, printer, *args):
        label = self._print_label_latex(printer, *args)
        # The extra {} brackets are needed to get matplotlib's latex
        # rendered to render this properly.
        return '{%s%s%s}' % (self.lbracket_latex, label, self.rbracket_latex)


class KetBase(StateBase):
    """Base class for Kets.

    This class defines the dual property and the brackets for printing. This
    is an abstract base class and you should not instantiate it directly,
    instead use Ket.
    """

    lbracket = '|'
    rbracket = '>'
    lbracket_pretty = prettyForm(_straight_bracket)
    rbracket_pretty = prettyForm(_rbracket)
    lbracket_latex = r'\left|'
    rbracket_latex = r'\right\rangle '

    @classmethod
    def default_args(self):
        return ("psi",)

    @classmethod
    def dual_class(self):
        return BraBase

    def __mul__(self, other):
        """KetBase*other"""
        from sympy.physics.quantum.operator import OuterProduct
        if isinstance(other, BraBase):
            return OuterProduct(self, other)
        else:
            return Expr.__mul__(self, other)

    def __rmul__(self, other):
        """other*KetBase"""
        from sympy.physics.quantum.innerproduct import InnerProduct
        if isinstance(other, BraBase):
            return InnerProduct(other, self)
        else:
            return Expr.__rmul__(self, other)

    #-------------------------------------------------------------------------
    # _eval_* methods
    #-------------------------------------------------------------------------

    def _eval_innerproduct(self, bra, **hints):
        """Evaluate the inner product betweeen this ket and a bra.

        This is called to compute <bra|ket>, where the ket is ``self``.

        This method will dispatch to sub-methods having the format::

            def _eval_innerproduct_BraClass(self, **hints):

        Subclasses should define these methods (one for each BraClass) to
        teach the ket how to take inner products with bras.
        """
        return dispatch_method(self, '_eval_innerproduct', bra, **hints)

    def _apply_operator(self, op, **options):
        """Apply an Operator to this Ket.

        This method will dispatch to methods having the format::

            def _apply_operator_OperatorName(op, **options):

        Subclasses should define these methods (one for each OperatorName) to
        teach the Ket how operators act on it.

        Parameters
        ==========
        op : Operator
            The Operator that is acting on the Ket.
        options : dict
            A dict of key/value pairs that control how the operator is applied
            to the Ket.
        """
        return dispatch_method(self, '_apply_operator', op, **options)

class BraBase(StateBase):
    """Base class for Bras.

    This class defines the dual property and the brackets for printing. This
    is an abstract base class and you should not instantiate it directly,
    instead use Bra.
    """

    lbracket = '<'
    rbracket = '|'
    lbracket_pretty = prettyForm(_lbracket)
    rbracket_pretty = prettyForm(_straight_bracket)
    lbracket_latex = r'\left\langle '
    rbracket_latex = r'\right|'

    @classmethod
    def _operators_to_state(self, ops, **options):
        state = self.dual_class().operators_to_state(ops, **options)
        return state.dual

    def _state_to_operators(self, op_classes, **options):
        return self.dual._state_to_operators(op_classes, **options)

    def _enumerate_state(self, num_states, **options):
        dual_states = self.dual._enumerate_state(num_states, **options)
        return map(lambda x: x.dual, dual_states)

    @classmethod
    def default_args(self):
        return self.dual_class().default_args()

    @classmethod
    def dual_class(self):
        return KetBase

    def __mul__(self, other):
        """BraBase*other"""
        from sympy.physics.quantum.innerproduct import InnerProduct
        if isinstance(other, KetBase):
            return InnerProduct(self, other)
        else:
            return Expr.__mul__(self, other)

    def __rmul__(self, other):
        """other*BraBase"""
        from sympy.physics.quantum.operator import OuterProduct
        if isinstance(other, KetBase):
            return OuterProduct(other, self)
        else:
            return Expr.__rmul__(self, other)

    def _represent(self, **options):
        """A default represent that uses the Ket's version."""
        from sympy.physics.quantum.dagger import Dagger
        return Dagger(self.dual._represent(**options))


class State(StateBase):
    """General abstract quantum state used as a base class for Ket and Bra."""
    pass



class Ket(State, KetBase):
    """A general time-independent Ket in quantum mechanics.

    Inherits from State and KetBase. This class should be used as the base
    class for all physical, time-independent Kets in a system. This class
    and its subclasses will be the main classes that users will use for
    expressing Kets in Dirac notation.

    Parameters
    ==========
    args : tuple
        The list of numbers or parameters that uniquely specify the
        ket. This will usually be its symbol or its quantum numbers. For
        time-dependent state, this will include the time.

    Examples
    ========

    Create a simple Ket and looking at its properties::

        >>> from sympy.physics.quantum import Ket, Bra
        >>> from sympy import symbols, I
        >>> k = Ket('psi')
        >>> k
        |psi>
        >>> k.hilbert_space
        H
        >>> k.is_commutative
        False
        >>> k.label
        (psi,)

    Ket's know about their associated bra::

        >>> k.dual
        <psi|
        >>> k.dual_class()
        <class 'sympy.physics.quantum.state.Bra'>

    Take a linear combination of two kets::

        >>> k0 = Ket(0)
        >>> k1 = Ket(1)
        >>> 2*I*k0 - 4*k1
        2*I*|0> - 4*|1>

    Compound labels are passed as tuples::

        >>> n, m = symbols('n,m')
        >>> k = Ket(n,m)
        >>> k
        |nm>

    References
    ==========

    [1] http://en.wikipedia.org/wiki/Bra-ket_notation
    """

    @classmethod
    def dual_class(self):
        return Bra

class Bra(State, BraBase):
    """A general time-independent Bra in quantum mechanics.

    Inherits from State and BraBase. A Bra is the dual of a Ket [1]. This
    class and its subclasses will be the main classes that users will use for
    expressing Bras in Dirac notation.

    Parameters
    ==========
    args : tuple
        The list of numbers or parameters that uniquely specify the
        ket. This will usually be its symbol or its quantum numbers. For
        time-dependent state, this will include the time.

    Examples
    ========

    Create a simple Bra and look at its properties::

        >>> from sympy.physics.quantum import Ket, Bra
        >>> from sympy import symbols, I
        >>> b = Bra('psi')
        >>> b
        <psi|
        >>> b.hilbert_space
        H
        >>> b.is_commutative
        False

    Bra's know about their dual Ket's::

        >>> b.dual
        |psi>
        >>> b.dual_class()
        <class 'sympy.physics.quantum.state.Ket'>

    Like Kets, Bras can have compound labels and be manipulated in a similar
    manner::

        >>> n, m = symbols('n,m')
        >>> b = Bra(n,m) - I*Bra(m,n)
        >>> b
        -I*<mn| + <nm|

    Symbols in a Bra can be substituted using ``.subs``::

        >>> b.subs(n,m)
        <mm| - I*<mm|

    References
    ==========

    [1] http://en.wikipedia.org/wiki/Bra-ket_notation
    """

    @classmethod
    def dual_class(self):
        return Ket

#-----------------------------------------------------------------------------
# Time dependent states, bras and kets.
#-----------------------------------------------------------------------------

class TimeDepState(StateBase):
    """Base class for a general time-dependent quantum state.

    This class is used as a base class for any time-dependent state. The main
    difference between this class and the time-independent state is that this
    class takes a second argument that is the time in addition to the usual
    label argument.

    Parameters
    ==========
    args : tuple
        The list of numbers or parameters that uniquely specify the
        ket. This will usually be its symbol or its quantum numbers. For
        time-dependent state, this will include the time as the final
        argument.
    """

    #-------------------------------------------------------------------------
    # Initialization
    #-------------------------------------------------------------------------

    @classmethod
    def default_args(self):
        return ("psi", "t")

    #-------------------------------------------------------------------------
    # Properties
    #-------------------------------------------------------------------------

    @property
    def label(self):
        """The label of the state."""
        return self.args[:-1]

    @property
    def time(self):
        """The time of the state."""
        return self.args[-1]

    #-------------------------------------------------------------------------
    # Printing
    #-------------------------------------------------------------------------

    def _print_time(self, printer, *args):
        return printer._print(self.time, *args)

    _print_time_repr = _print_time
    _print_time_latex = _print_time

    def _print_time_pretty(self, printer, *args):
        pform = printer._print(self.time, *args)
        return pform

    def _print_contents(self, printer, *args):
        label = self._print_label(printer, *args)
        time = self._print_time(printer, *args)
        return '%s%s;%s%s' % (self.lbracket, label, time, self.rbracket)

    def _print_contents_repr(self, printer, *args):
        label = self._print_label_repr(printer, *args)
        time = self._print_time_repr(printer, *args)
        return '%s,%s' % (label, time)

    def _print_contents_pretty(self, printer, *args):
        pform = self._print_label_pretty(printer, *args)
        pform = prettyForm(*pform.left((self.lbracket_pretty)))
        pform = prettyForm(*pform.right((';')))
        nextpform = self._print_time_pretty(printer, *args)
        pform = prettyForm(*pform.right((nextpform)))
        pform = prettyForm(*pform.right((self.rbracket_pretty)))
        return pform

    def _print_contents_latex(self, printer, *args):
        label = self._print_label_latex(printer, *args)
        time = self._print_time_latex(printer, *args)
        # The extra {} brackets are needed to get matplotlib's latex
        # rendered to render this properly.
        return '{%s%s;%s%s}' %\
            (self.lbracket_latex, label, time, self.rbracket_latex)


class TimeDepKet(TimeDepState, KetBase):
    """General time-dependent Ket in quantum mechanics.

    This inherits from TimeDepState and KetBase and is the main class that
    should be used for Kets that vary with time. Its dual is a TimeDepBra.

    Parameters
    ==========
    args : tuple
        The list of numbers or parameters that uniquely specify the
        ket. This will usually be its symbol or its quantum numbers. For
        time-dependent state, this will include the time as the final
        argument.

    Examples
    ========

    Create a TimeDepKet and look at its attributes::

        >>> from sympy.physics.quantum import TimeDepKet
        >>> k = TimeDepKet('psi', 't')
        >>> k
        |psi;t>
        >>> k.time
        t
        >>> k.label
        (psi,)
        >>> k.hilbert_space
        H

    TimeDepKets know about their dual bra::

        >>> k.dual
        <psi;t|
        >>> k.dual_class()
        <class 'sympy.physics.quantum.state.TimeDepBra'>
    """

    @classmethod
    def dual_class(self):
        return TimeDepBra


class TimeDepBra(TimeDepState, BraBase):
    """General time-dependent Bra in quantum mechanics.

    This inherits from TimeDepState and BraBase and is the main class that
    should be used for Bras that vary with time. Its dual is a TimeDepBra.

    Parameters
    ==========
    args : tuple
        The list of numbers or parameters that uniquely specify the
        ket. This will usually be its symbol or its quantum numbers. For
        time-dependent state, this will include the time as the final
        argument.

    Examples
    ========

        >>> from sympy.physics.quantum import TimeDepBra
        >>> from sympy import symbols, I
        >>> b = TimeDepBra('psi', 't')
        >>> b
        <psi;t|
        >>> b.time
        t
        >>> b.label
        (psi,)
        >>> b.hilbert_space
        H
        >>> b.dual
        |psi;t>
    """

    @classmethod
    def dual_class(self):
        return TimeDepKet

class Wavefunction(Function):
    """Class for representations in continuous bases

    This class takes an expression and coordinates in its
    constructor. It can be used to easily calculate normalizations and
    probabilities.

    Parameters
    ==========

    expr : Expr
           The expression representing the functional form of the w.f.

    coords : Symbol or tuple
           The coordinates to be integrated over, and their bounds

    Examples
    ========

    Particle in a box, specifying bounds in the more primitive way of
    using Piecewise

    >>> from sympy import Symbol, Piecewise, pi, N
    >>> from sympy.functions import sqrt, sin
    >>> from sympy.physics.quantum.state import Wavefunction
    >>> x = Symbol('x')
    >>> n = 1
    >>> L = 1
    >>> g = Piecewise((0, x < 0), (0, x > L), (sqrt(2//L)*sin(n*pi*x/L), True))
    >>> f = Wavefunction(g, x)
    >>> f.norm
    1
    >>> f.is_normalized
    True
    >>> p = f.prob()
    >>> p(0)
    0
    >>> p(L)
    0
    >>> p(0.5)
    2
    >>> p(0.85*L)
    2*sin(0.85*pi)**2
    >>> N(p(0.85*L))
    0.412214747707527

    Additionally, you can specify the bounds of the function and the
    indices in a more compact way.

    >>> from sympy import symbols, pi, diff
    >>> from sympy.functions import sqrt, sin
    >>> from sympy.physics.quantum.state import Wavefunction
    >>> x, L = symbols('x,L', real=True)
    >>> n = symbols('n', integer=True)
    >>> g = sqrt(2/L)*sin(n*pi*x/L)
    >>> f = Wavefunction(g, (x, 0, L))
    >>> f.norm
    1
    >>> f(L+1)
    0
    >>> f(L-1)
    sqrt(2)*sqrt(1/L)*sin(pi*n*(L - 1)/L)
    >>> f(-1)
    0
    >>> f(0.85)
    sqrt(2)*sqrt(1/L)*sin(0.85*pi*n/L)
    >>> f(0.85, n=1, L=1)
    sqrt(2)*sin(0.85*pi)
    >>> f.is_commutative
    False

    All arguments are automatically sympified, so you can define the
    variables as strings rather than symbols
    >>> expr = x**2
    >>> f = Wavefunction(expr, 'x')
    >>> type(f.variables[0])
    <class 'sympy.core.symbol.Symbol'>

    Derivatives of Wavefunctions will return Wavefunctions
    >>> diff(f, x)
    Wavefunction(2*x, x)

    """

    #Any passed tuples for coordinates and their bounds need to be
    #converted to Tuples before Function's constructor is called, to
    #avoid errors from calling is_Float in the constructor
    def __new__(cls, *args, **options):
        new_args = [None for i in args]
        ct = 0
        for arg in args:
            if isinstance(arg, tuple):
                new_args[ct] = Tuple(*arg)
            else:
                new_args[ct] = arg
            ct+=1

        return super(Function, cls).__new__(cls, *new_args, **options)

    def __call__(self, *args, **options):
        var = self.variables

        if len(args) != len(var):
            raise NotImplementedError("Incorrect number of arguments to function!")

        ct = 0
        #If the passed value is outside the specified bounds, return 0
        for v in var:
            lower,upper = self.limits[v]

            #Do the comparison to limits only if the passed symbol is actually
            #a symbol present in the limits;
            #Had problems with a comparison of x > L
            if isinstance(args[ct], Expr) and \
                   not (lower in args[ct].free_symbols \
                        or upper in args[ct].free_symbols):
                continue

            if args[ct] < lower or args[ct] > upper:
                return 0

            ct+=1

        expr = self.expr

        #Allows user to make a call like f(2, 4, m=1, n=1)
        for symbol in list(expr.free_symbols):
            if str(symbol) in options.keys():
                val = options[str(symbol)]
                expr = expr.subs(symbol, val)

        return expr.subs(tuple(zip(var, args)))

    def _eval_derivative(self, symbol):
        expr = self.expr
        deriv = expr._eval_derivative(symbol)

        return Wavefunction(deriv, *self.args[1:])

    def _eval_dagger(self):
        return conjugate(self)

    def _eval_conjugate(self):
        return Wavefunction(conjugate(self.expr), *self.args[1:])

    @property
    def free_symbols(self):
        return self.expr.free_symbols

    @property
    def is_commutative(self):
        """
        Override Function's is_commutative so that order is preserved
        in represented expressions
        """
        return False

    @classmethod
    def eval(self, *args):
        return None

    @property
    def variables(self):
        """
        Return the coordinates which the wavefunction depends on

        Examples
        ========

        >>> from sympy.physics.quantum.state import Wavefunction
        >>> from sympy import symbols
        >>> x,y = symbols('x,y')
        >>> f = Wavefunction(x*y, x, y)
        >>> f.variables
        (x, y)
        >>> g = Wavefunction(x*y, x)
        >>> g.variables
        (x,)

        """
        var = [g[0] if isinstance(g, Tuple) else g for g in self._args[1:]]
        return tuple(var)

    @property
    def limits(self):
        """
        Return the limits of the coordinates which the w.f. depends on
        If no limits are specified, defaults to (-oo, oo)

        Examples
        ========

        >>> from sympy.physics.quantum.state import Wavefunction
        >>> from sympy import symbols
        >>> x, y = symbols('x, y')
        >>> f = Wavefunction(x**2, (x, 0, 1))
        >>> f.limits
        {x: (0, 1)}
        >>> f = Wavefunction(x**2, x)
        >>> f.limits
        {x: (-oo, oo)}
        >>> f = Wavefunction(x**2 + y**2, x, (y, -1, 2))
        >>> f.limits
        {x: (-oo, oo), y: (-1, 2)}

        """
        limits = [(g[1], g[2]) if isinstance(g, Tuple) else (-oo, oo) \
                  for g in self._args[1:]]
        return dict(zip(self.variables, tuple(limits)))

    @property
    def expr(self):
        """
        Return the expression which is the functional form of the
        Wavefunction

        Examples
        ========

        >>> from sympy.physics.quantum.state import Wavefunction
        >>> from sympy import symbols
        >>> x, y = symbols('x, y')
        >>> f = Wavefunction(x**2, x)
        >>> f.expr
        x**2

        """
        return self._args[0]

    @property
    def is_normalized(self):
        """
        Returns true if the Wavefunction is properly normalized

        Examples
        ========

        >>> from sympy import symbols, pi
        >>> from sympy.functions import sqrt, sin
        >>> from sympy.physics.quantum.state import Wavefunction
        >>> x, L = symbols('x,L', real=True)
        >>> n = symbols('n', integer=True)
        >>> g = sqrt(2/L)*sin(n*pi*x/L)
        >>> f = Wavefunction(g, (x, 0, L))
        >>> f.is_normalized
        True

        """

        return (self.norm == 1.0)

    @property
    @cacheit
    def norm(self):
        """
        Return the normalization of the specified functional form.

        This function integrates over the coordinates of the Wavefunction,
        with the bounds specified.

        Examples
        ========

        >>> from sympy import symbols, pi
        >>> from sympy.functions import sqrt, sin
        >>> from sympy.physics.quantum.state import Wavefunction
        >>> x, L = symbols('x,L', real=True)
        >>> n = symbols('n', integer=True)
        >>> g = sqrt(2/L)*sin(n*pi*x/L)
        >>> f = Wavefunction(g, (x, 0, L))
        >>> f.norm
        1
        >>> g = sin(n*pi*x/L)
        >>> f = Wavefunction(g, (x, 0, L))
        >>> f.norm
        sqrt(2)*sqrt(L)/2

        """

        exp = self.expr*conjugate(self.expr)
        var = self.variables
        limits = self.limits

        for v in var:
            curr_limits = limits[v]
            exp = integrate(exp, (v, curr_limits[0], curr_limits[1]))

        return sqrt(exp)

    def normalize(self):
        """
        Return a normalized version of the Wavefunction

        Examples
        ========

        >>> from sympy import symbols, pi
        >>> from sympy.functions import sqrt, sin
        >>> from sympy.physics.quantum.state import Wavefunction
        >>> x, L = symbols('x,L', real=True)
        >>> n = symbols('n', integer=True)
        >>> g = sin(n*pi*x/L)
        >>> f = Wavefunction(g, (x, 0, L))
        >>> f.normalize()
        Wavefunction(sqrt(2)*sin(pi*n*x/L)/sqrt(L), (x, 0, L))

        """
        const = self.norm

        if const == oo:
            raise NotImplementedError("The function is not normalizable!")
        else:
            return Wavefunction((const)**(-1)*self.expr, *self.args[1:])

    def prob(self):
        """
        Return the absolute magnitude of the w.f., |psi(x)|^2

        Examples
        ========

        >>> from sympy import symbols, pi
        >>> from sympy.functions import sqrt, sin
        >>> from sympy.physics.quantum.state import Wavefunction
        >>> x, L = symbols('x,L', real=True)
        >>> n = symbols('n', integer=True)
        >>> g = sin(n*pi*x/L)
        >>> f = Wavefunction(g, (x, 0, L))
        >>> f.prob()
        Wavefunction(sin(pi*n*x/L)**2, x)

        """

        return Wavefunction(self.expr*conjugate(self.expr), *self.variables)
