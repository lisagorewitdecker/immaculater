"""Defines ViewFilter and its subclasses.

These allow you to filter out completed, deleted, and inactive items.

The variable CLS_BY_UI_NAME allows you to find a view filter given its
User-facing name.
"""

from . import action
from . import ctx
from . import folder
from . import prj


class ViewFilter(object):
  """Shall we show completed items?  Inactive contexts? Etc."""

  __pychecker__ = 'unusednames=cls'
  @classmethod
  def ViewFilterUINames(cls):
    """Returns all the different aliases of this view filter.

    Returns:
      tuple(basestring)
    """
    raise NotImplementedError('ViewFilterUINames')

  def __init__(self, action_to_project, action_to_context):
    """Args:
      action_to_project: a function (Action,)->Prj raising
        ValueError if the given action does not exist.

      action_to_context: a function (Action,)->Ctx raising ValueError if the
        given action's context should exist but does not.
    """
    self.action_to_project = action_to_project
    self.action_to_context = action_to_context

  def Show(self, item):
    """Returns True iff item should be displayed.

    Args:
      item: Action|Prj|Ctx|Folder
    Returns:
      bool
    """
    if isinstance(item, action.Action):
      return self.ShowAction(item)
    if isinstance(item, prj.Prj):
      return self.ShowProject(item)
    if isinstance(item, ctx.Ctx):
      return self.ShowContext(item)
    if isinstance(item, folder.Folder):
      return self.ShowFolder(item)

  def ShowAction(self, an_action):
    """Returns True iff the Action should be displayed.

    Args:
      item: Action
    Returns:
      bool
    """
    raise NotImplementedError

  def ShowProject(self, project):
    """Returns True iff the Prj should be displayed.

    Args:
      item: Prj
    Returns:
      bool
    """
    raise NotImplementedError

  def ShowFolder(self, a_folder):
    """Returns True iff the Folder should be displayed.

    Args:
      item: Folder
    Returns:
      bool
    """
    raise NotImplementedError

  def ShowContext(self, context):
    """Returns True iff the Ctx should be displayed.

    Args:
      item: Ctx
    Returns:
      bool
    """
    raise NotImplementedError


class ShowAll(ViewFilter):
  """Shows all items -- doesn't filter any out."""

  @classmethod
  def ViewFilterUINames(cls):
    return ('all_even_deleted',)

  def ShowAction(self, an_action):
    return True

  def ShowProject(self, project):
    return True

  def ShowFolder(self, a_folder):
    return True

  def ShowContext(self, context):
    return True


class ShowNotDeleted(ViewFilter):
  """Shows items that are not deleted.  This WILL show inactive and
  completed items.
  """

  @classmethod
  def ViewFilterUINames(cls):
    return ('all', 'default')

  def ShowAction(self, an_action):
    return not an_action.is_deleted

  def ShowProject(self, project):
    return not project.is_deleted

  def ShowFolder(self, a_folder):
    return not a_folder.is_deleted

  def ShowContext(self, context):
    return not context.is_deleted


class ShowNotFinalized(ViewFilter):
  """Shows items that are not deleted or completed.  This WILL show
  inactive items.
  """

  @classmethod
  def ViewFilterUINames(cls):
    return ('incomplete',)

  def __init__(self, *args):
    super(ShowNotFinalized, self).__init__(*args)
    self.deleted_viewfilter = ShowNotDeleted(*args)

  def ShowAction(self, an_action):
    containing_project = self.action_to_project(an_action)
    return (self.deleted_viewfilter.ShowAction(an_action)
            and not an_action.is_complete
            and not containing_project.is_complete)

  def ShowProject(self, project):
    return (self.deleted_viewfilter.ShowProject(project)
            and not project.is_complete)

  def ShowFolder(self, a_folder):
    return self.deleted_viewfilter.ShowFolder(a_folder)

  def ShowContext(self, context):
    return self.deleted_viewfilter.ShowContext(context)


class ShowActionable(ViewFilter):
  """Shows items that are not deleted, completed, or inactive."""

  @classmethod
  def ViewFilterUINames(cls):
    return ('actionable',)

  def __init__(self, *args):
    super(ShowActionable, self).__init__(*args)
    self.not_finalized_viewfilter = ShowNotFinalized(*args)

  def ShowAction(self, an_action):
    containing_context = self.action_to_context(an_action)
    return (self.not_finalized_viewfilter.ShowAction(an_action)
            and (containing_context is None or containing_context.is_active)
            and self.action_to_project(an_action).is_active)

  def ShowProject(self, project):
    return (self.not_finalized_viewfilter.ShowProject(project)
            and project.is_active)

  def ShowFolder(self, a_folder):
    return self.not_finalized_viewfilter.ShowFolder(a_folder)

  def ShowContext(self, context):
    return (self.not_finalized_viewfilter.ShowContext(context)
            and context.is_active)


class ShowNeedingReview(ViewFilter):
  """Shows items that are not deleted, completed, reviewed, or inactive.

  Only Projects need review -- shows Actions in reviewed Projects.
  """

  @classmethod
  def ViewFilterUINames(cls):
    return ('needing_review',)

  def __init__(self, *args):
    super(ShowNeedingReview, self).__init__(*args)
    self.not_finalized_viewfilter = ShowNotFinalized(*args)

  def ShowAction(self, an_action):
    return self.not_finalized_viewfilter.ShowAction(an_action)

  def ShowProject(self, project):
    return (self.not_finalized_viewfilter.ShowProject(project)
            and project.NeedsReview() and project.is_active)

  def ShowFolder(self, a_folder):
    return self.not_finalized_viewfilter.ShowFolder(a_folder)

  def ShowContext(self, context):
    return self.not_finalized_viewfilter.ShowContext(context)


class ShowInactiveIncomplete(ViewFilter):
  """Shows undeleted, incomplete items that are in inactive Projects or Contexts."""

  @classmethod
  def ViewFilterUINames(cls):
    return ('inactive_and_incomplete',)

  def __init__(self, *args):
    super(ShowInactiveIncomplete, self).__init__(*args)
    self.not_finalized_viewfilter = ShowNotFinalized(*args)

  def ShowAction(self, an_action):
    containing_project = self.action_to_project(an_action)
    containing_context = self.action_to_context(an_action)
    return self.not_finalized_viewfilter.ShowAction(an_action) and (
      not containing_project.is_active or (
        containing_context is not None and not containing_context.is_active))

  def ShowProject(self, project):
    return (self.not_finalized_viewfilter.ShowProject(project)
            and not project.is_active)

  def ShowFolder(self, a_folder):
    # TODO(chandler): Show it only if a descendant is inactive and incomplete?
    return self.not_finalized_viewfilter.ShowFolder(a_folder)

  def ShowContext(self, context):
    return self.not_finalized_viewfilter.ShowContext(context) and (
      not context.is_active)


CLS_BY_UI_NAME = {}

for view_filter_cls in (
    ShowAll,
    ShowNotDeleted,
    ShowNotFinalized,
    ShowActionable,
    ShowNeedingReview,
    ShowInactiveIncomplete):
  for name in view_filter_cls.ViewFilterUINames():
    assert name not in CLS_BY_UI_NAME, name
    CLS_BY_UI_NAME[name] = view_filter_cls