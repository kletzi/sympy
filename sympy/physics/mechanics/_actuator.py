"""Implementations of actuators for linked force and torque application.

Notes
=====

This module is experimental and so is named with a leading underscore to
indicate that the API is not yet stabilized and could be subject to breaking
changes.

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from sympy.core.backend import USE_SYMENGINE
from sympy.physics.mechanics import (
    PinJoint,
    ReferenceFrame,
    RigidBody,
    Torque,
    Vector,
)
from sympy.physics.mechanics._pathway import PathwayBase

if USE_SYMENGINE:
    from sympy.core.backend import Basic as ExprType
else:
    from sympy.core.expr import Expr as ExprType

if TYPE_CHECKING:
    from sympy.physics.mechanics.loads import LoadBase


__all__ = ['ForceActuator']


class ActuatorBase(ABC):
    """Abstract base class for all actuator classes to inherit from.

    Notes
    =====

    Instances of this class cannot be directly instantiated by users. However,
    it can be used to created custom actuator types through subclassing.

    """

    def __init__(self) -> None:
        """Initializer for ``ActuatorBase``."""
        pass

    @abstractmethod
    def to_loads(self) -> list[LoadBase]:
        """Loads required by the equations of motion method classes.

        Explanation
        ===========

        ``KanesMethod`` requires a list of ``Point``-``Vector`` tuples to be
        passed to the ``loads`` parameters of its ``kanes_equations`` method
        when constructing the equations of motion. This method acts as a
        utility to produce the correctly-structred pairs of points and vectors
        required so that these can be easily concatenated with other items in
        the list of loads and passed to ``KanesMethod.kanes_equations``. These
        loads are also in the correct form to also be passed to the other
        equations of motion method classes, e.g. ``LagrangesMethod``.

        """
        pass

    def __repr__(self) -> str:
        """Default representation of an actuator."""
        return f'{self.__class__.__name__}()'


class ForceActuator(ActuatorBase):
    """Force-producing actuator.

    Explanation
    ===========

    A ``ForceActuator`` is an actuator that produces a (expansile) force along
    its length.

    Examples
    ========

    As the ``_actuator.py`` module is experimental, it is not yet part of the
    ``sympy.physics.mechanics`` namespace. ``ForceActuator`` must therefore be
    imported directly from the ``sympy.physics.mechanics._actuator`` module.

    >>> from sympy.physics.mechanics._actuator import ForceActuator

    This is similarly the case for imports from the ``_pathway.py`` module like
    ``LinearPathway``.

    >>> from sympy.physics.mechanics._pathway import LinearPathway

    To construct an actuator, an expression (or symbol) must be supplied to
    represent the force it can produce, alongside a pathway specifying its line
    of action. Let's also create a global reference frame and spatially fix one
    of the points in it while setting the other to be positioned such that it
    can freely move in the frame's x direction specified by the coordinate
    ``q``.

    >>> from sympy import Symbol
    >>> from sympy.physics.mechanics import Point, ReferenceFrame
    >>> from sympy.physics.vector import dynamicsymbols
    >>> N = ReferenceFrame('N')
    >>> q = dynamicsymbols('q')
    >>> force = Symbol('F')
    >>> pA, pB = Point('pA'), Point('pB')
    >>> pA.set_vel(N, 0)
    >>> pB.set_pos(pA, q * N.x)
    >>> pB.pos_from(pA)
    q(t)*N.x
    >>> linear_pathway = LinearPathway(pA, pB)
    >>> actuator = ForceActuator(force, linear_pathway)
    >>> actuator
    ForceActuator(F, LinearPathway(pA, pB))

    Parameters
    ==========

    force : Expr
        The scalar expression defining the (expansile) force that the actuator
        produces.
    pathway : PathwayBase
        The pathway that the actuator follows. This must be an instance of a
        concrete subclass of ``PathwayBase``, e.g. ``LinearPathway``.

    """

    def __init__(
        self,
        force: ExprType,
        pathway: PathwayBase,
    ) -> None:
        """Initializer for ``ForceActuator``.

        Parameters
        ==========

        force : Expr
            The scalar expression defining the (expansile) force that the
            actuator produces.
        pathway : PathwayBase
            The pathway that the actuator follows. This must be an instance of
            a concrete subclass of ``PathwayBase``, e.g. ``LinearPathway``.

        """
        self.force = force
        self.pathway = pathway
        super().__init__()

    @property
    def force(self) -> ExprType:
        """The magnitude of the force produced by the actuator."""
        return self._force

    @force.setter
    def force(self, force: ExprType) -> None:
        if not isinstance(force, ExprType):
            msg = (
                f'Value {repr(force)} passed to `force` was of type '
                f'{type(force)}, must be {ExprType}.'
            )
            raise TypeError(msg)
        self._force = force

    @property
    def pathway(self) -> PathwayBase:
        """The ``Pathway`` defining the actuator's line of action."""
        return self._pathway

    @pathway.setter
    def pathway(self, pathway: PathwayBase) -> None:
        if not isinstance(pathway, PathwayBase):
            msg = (
                f'Value {repr(pathway)} passed to `pathway` was of type '
                f'{type(pathway)}, must be {PathwayBase}.'
            )
            raise TypeError(msg)
        self._pathway = pathway

    def to_loads(self) -> list[LoadBase]:
        """Loads required by the equations of motion method classes.

        Explanation
        ===========

        ``KanesMethod`` requires a list of ``Point``-``Vector`` tuples to be
        passed to the ``loads`` parameters of its ``kanes_equations`` method
        when constructing the equations of motion. This method acts as a
        utility to produce the correctly-structred pairs of points and vectors
        required so that these can be easily concatenated with other items in
        the list of loads and passed to ``KanesMethod.kanes_equations``. These
        loads are also in the correct form to also be passed to the other
        equations of motion method classes, e.g. ``LagrangesMethod``.

        Examples
        ========

        The below example shows how to generate the loads produced by a force
        actuator that follows a linear pathway. In this example we'll assume
        that the force actuator is being used to model a simple linear spring.
        First, create a linear pathway between two points separated by the
        coordinate ``q`` in the ``x`` direction of the global frame ``N``.

        >>> from sympy.physics.mechanics import Point, ReferenceFrame
        >>> from sympy.physics.mechanics._pathway import LinearPathway
        >>> from sympy.physics.vector import dynamicsymbols
        >>> q = dynamicsymbols('q')
        >>> N = ReferenceFrame('N')
        >>> pA, pB = Point('pA'), Point('pB')
        >>> pB.set_pos(pA, q * N.x)
        >>> pathway = LinearPathway(pA, pB)

        Now create a symbol ``k`` to describe the spring's stiffness and
        instantiate a force actuator that produces a (contractile) force
        proportional to both the spring's stiffness and the pathway's length.
        Note that actuator classes use the sign convention that expansile
        forces are positive, so for a spring to produce a contractile force the
        spring force needs to be calculated as the negative for the stiffness
        multiplied by the length.

        >>> from sympy import Symbol
        >>> from sympy.physics.mechanics._actuator import ForceActuator
        >>> stiffness = Symbol('k')
        >>> spring_force = -stiffness * pathway.length
        >>> spring = ForceActuator(spring_force, pathway)

        The forces produced by the spring can be generated in the list of loads
        form that ``KanesMethod`` (and other equations of motion methods)
        requires by calling the ``to_loads`` method.

        >>> spring.to_loads()
        [(pA, k*q(t)*N.x), (pB, - k*q(t)*N.x)]

        A simple linear damper can be modeled in a similar way. Create another
        symbol ``c`` to describe the dampers damping coefficient. This time
        instantiate a force actuator that produces a force proportional to both
        the damper's damping coefficient and the pathway's extension velocity.
        Note that the damping force is negative as it acts in the opposite
        direction to which the damper is changing in length.

        >>> damping_coefficient = Symbol('c')
        >>> damping_force = -damping_coefficient * pathway.extension_velocity
        >>> damper = ForceActuator(damping_force, pathway)

        Again, the forces produces by the damper can be generated by calling
        the ``to_loads`` method.

        >>> damper.to_loads()
        [(pA, c*q(t)**2*Derivative(q(t), t)/q(t)**2*N.x),
         (pB, - c*q(t)**2*Derivative(q(t), t)/q(t)**2*N.x)]

        """
        return self.pathway.compute_loads(self.force)

    def __repr__(self) -> str:
        """Representation of a ``ForceActuator``."""
        return f'{self.__class__.__name__}({self.force}, {self.pathway})'


class TorqueActuator(ActuatorBase):
    """Torque-producing actuator.

    Explanation
    ===========

    A ``TorqueActuator`` is an actuator that produces a pair of equal and
    opposite torques on a pair of bodies.

    Examples
    ========

    As the ``_actuator.py`` module is experimental, it is not yet part of the
    ``sympy.physics.mechanics`` namespace. ``TorqueActuator`` must therefore be
    imported directly from the ``sympy.physics.mechanics._actuator`` module.

    >>> from sympy.physics.mechanics._actuator import TorqueActuator

    To construct a torque actuator, an expression (or symbol) must be supplied
    to represent the torque it can produce, alongside a vector specifying the
    axis about which the torque will act, and a pair of frames on which the
    torque will act.

    >>> from sympy import Symbol
    >>> from sympy.physics.mechanics import ReferenceFrame, RigidBody
    >>> N = ReferenceFrame('N')
    >>> A = ReferenceFrame('A')
    >>> torque = Symbol('T')
    >>> axis = N.z
    >>> parent = RigidBody('parent', frame=N)
    >>> child = RigidBody('child', frame=A)
    >>> bodies = (parent, child)
    >>> actuator = TorqueActuator(torque, axis, *bodies)
    >>> actuator
    TorqueActuator(T, axis=N.z, target_frame=N, reaction_frame=A)

    Note that because torques actually act on frames, not bodies,
    ``TorqueActuator`` will extract the frame associated with a ``RigidBody``
    when one is passed instead of a ``ReferenceFrame``.

    Parameters
    ==========

    torque : Expr
        The scalar expression defining the torque that the actuator produces.
    axis : Vector
        The axis about which the actuator applies torques.
    target_frame : ReferenceFrame | RigidBody
        The primary frame on which the actuator will apply the torque.
    reaction_frame : ReferenceFrame | RigidBody | None
        The secondary frame on which the actuator will apply the torque. Note
        that the (equal and opposite) reaction torque is applied to this frame.

    """

    def __init__(
        self,
        torque: ExprType,
        axis: Vector,
        target_frame: ReferenceFrame | RigidBody,
        reaction_frame: ReferenceFrame | RigidBody | None = None,
    ) -> None:
        """Initializer for ``TorqueActuator``.

        Parameters
        ==========

        torque : Expr
            The scalar expression defining the torque that the actuator
            produces.
        axis : Vector
            The axis about which the actuator applies torques.
        target_frame : ReferenceFrame | RigidBody
            The primary frame on which the actuator will apply the torque.
        reaction_frame : ReferenceFrame | RigidBody | None
           The secondary frame on which the actuator will apply the torque.
           Note that the (equal and opposite) reaction torque is applied to
           this frame.

        """
        self.torque = torque
        self.axis = axis
        self.target_frame = target_frame  # type: ignore
        self.reaction_frame = reaction_frame  # type: ignore
        super().__init__()

    @classmethod
    def at_pin_joint(
        cls,
        torque: ExprType,
        pin_joint: PinJoint,
    ) -> TorqueActuator:
        """Alternate construtor to instantiate from a ``PinJoint`` instance.

        Examples
        ========

        To create a pin joint the ``PinJoint`` class requires a name, parent
        body, and child body to be passed to its constructor. It is also
        possible to control the joint axis using the ``joint_axis`` keyword
        argument. In this example let's use the parent body's reference frame's
        z-axis as the joint axis.

        >>> from sympy.physics.mechanics import (PinJoint, ReferenceFrame,
        ... RigidBody)
        >>> from sympy.physics.mechanics._actuator import TorqueActuator
        >>> N = ReferenceFrame('N')
        >>> A = ReferenceFrame('A')
        >>> parent = RigidBody('parent', frame=N)
        >>> child = RigidBody('child', frame=A)
        >>> pin_joint = PinJoint(
        ...     'pin',
        ...     parent,
        ...     child,
        ...     joint_axis=N.z,
        ... )

        Let's also create a symbol ``T`` that will represent the torque applied
        by the torque actuator.

        >>> from sympy import Symbol
        >>> torque = Symbol('T')

        To create the torque actuator from the ``torque`` and ``pin_joint``
        variables previously instantiated, these can be passed to the alternate
        constructor class method ``at_pin_joint`` of the ``TorqueActuator``
        class.

        >>> actuator = TorqueActuator.at_pin_joint(torque, pin_joint)
        >>> actuator
        TorqueActuator(T, axis=N.z, target_frame=N, reaction_frame=A)

        Parameters
        ==========

        torque : Expr
            The scalar expression defining the torque that the actuator
            produces.
        pin_joint : PinJoint
            The pin joint, and by association the parent and child bodies, on
            which the torque actuator will act. The pair of bodies acted upon
            by the torque actuator are the parent and child bodies of the pin
            joint, with the child acting as the reaction body. The pin joint's
            axis is used as the axis about which the torque actuator will apply
            its torque.

        """
        if not isinstance(pin_joint, PinJoint):
            msg = (
                f'Value {repr(pin_joint)} passed to `pin_joint` was of type '
                f'{type(pin_joint)}, must be {PinJoint}.'
            )
            raise TypeError(msg)
        return cls(
            torque,
            pin_joint.joint_axis,
            pin_joint.parent_interframe,
            pin_joint.child_interframe,
        )

    @property
    def torque(self) -> ExprType:
        """The magnitude of the torque produced by the actuator."""
        return self._torque

    @torque.setter
    def torque(self, torque: ExprType) -> None:
        if not isinstance(torque, ExprType):
            msg = (
                f'Value {repr(torque)} passed to `torque` was of type '
                f'{type(torque)}, must be {ExprType}.'
            )
            raise TypeError(msg)
        self._torque = torque

    @property
    def axis(self) -> Vector:
        """The axis about which the torque acts."""
        return self._axis

    @axis.setter
    def axis(self, axis: Vector) -> None:
        if not isinstance(axis, Vector):
            msg = (
                f'Value {repr(axis)} passed to `axis` was of type '
                f'{type(axis)}, must be {Vector}.'
            )
            raise TypeError(msg)
        self._axis = axis

    @property
    def target_frame(self) -> ReferenceFrame:
        """The primary reference frames on which the torque will act."""
        return self._target_frame

    @target_frame.setter
    def target_frame(self, target_frame: ReferenceFrame | RigidBody) -> None:
        if isinstance(target_frame, RigidBody):
            target_frame = target_frame.frame
        elif not isinstance(target_frame, ReferenceFrame):
            msg = (
                f'Value {repr(target_frame)} passed to `target_frame` was of '
                f'type 'f'{type(target_frame)}, must be {ReferenceFrame}.'
            )
            raise TypeError(msg)
        self._target_frame: ReferenceFrame = target_frame  # type: ignore

    @property
    def reaction_frame(self) -> ReferenceFrame | None:
        """The primary reference frames on which the torque will act."""
        return self._reaction_frame

    @reaction_frame.setter
    def reaction_frame(self, reaction_frame: ReferenceFrame | RigidBody | None) -> None:
        if isinstance(reaction_frame, RigidBody):
            reaction_frame = reaction_frame.frame
        elif (
            not isinstance(reaction_frame, ReferenceFrame)
            and reaction_frame is not None
        ):
            msg = (
                f'Value {repr(reaction_frame)} passed to `reaction_frame` was of '
                f'type 'f'{type(reaction_frame)}, must be {ReferenceFrame}.'
            )
            raise TypeError(msg)
        self._reaction_frame: ReferenceFrame | None = reaction_frame  # type: ignore

    def to_loads(self) -> list[LoadBase]:
        """Loads required by the equations of motion method classes.

        Explanation
        ===========

        ``KanesMethod`` requires a list of ``Point``-``Vector`` tuples to be
        passed to the ``loads`` parameters of its ``kanes_equations`` method
        when constructing the equations of motion. This method acts as a
        utility to produce the correctly-structred pairs of points and vectors
        required so that these can be easily concatenated with other items in
        the list of loads and passed to ``KanesMethod.kanes_equations``. These
        loads are also in the correct form to also be passed to the other
        equations of motion method classes, e.g. ``LagrangesMethod``.

        Examples
        ========

        The below example shows how to generate the loads produced by a torque
        actuator that acts on a pair of bodies attached by a pin joint.

        >>> from sympy import Symbol
        >>> from sympy.physics.mechanics import (PinJoint, ReferenceFrame,
        ... RigidBody)
        >>> from sympy.physics.mechanics._actuator import TorqueActuator
        >>> torque = Symbol('T')
        >>> N = ReferenceFrame('N')
        >>> A = ReferenceFrame('A')
        >>> parent = RigidBody('parent', frame=N)
        >>> child = RigidBody('child', frame=A)
        >>> pin_joint = PinJoint(
        ...     'pin',
        ...     parent,
        ...     child,
        ...     joint_axis=N.z,
        ... )
        >>> actuator = TorqueActuator.at_pin_joint(torque, pin_joint)

        The forces produces by the damper can be generated by calling the
        ``to_loads`` method.

        >>> actuator.to_loads()
        [(N, T*N.z), (A, - T*N.z)]

        Alternatively, if a torque actuator is created without a reaction frame
        then the loads returned by the ``to_loads`` method will contain just
        the single load acting on the target frame.

        >>> actuator = TorqueActuator(torque, N.z, N)
        >>> actuator.to_loads()
        [(N, T*N.z)]

        """
        loads: list[LoadBase] = [
            Torque(self.target_frame, self.torque * self.axis),
        ]
        if self.reaction_frame is not None:
            loads.append(Torque(self.reaction_frame, -self.torque * self.axis))
        return loads

    def __repr__(self) -> str:
        """Representation of a ``TorqueActuator``."""
        string = (
            f'{self.__class__.__name__}({self.torque}, axis={self.axis}, '
            f'target_frame={self.target_frame}'
        )
        if self.reaction_frame is not None:
            string += f', reaction_frame={self.reaction_frame})'
        else:
            string += ')'
        return string