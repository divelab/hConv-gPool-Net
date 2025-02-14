import tensorflow as tf
import tensorpack as tp


def graph_pool(adj_m, outs, kernel, scope):
    with tf.variable_scope(scope):
        k = outs.shape[1].value // kernel
        scores = conv1d(outs, 1, 1, 'scores', None, False)
        scores = tf.abs(scores, 'abs')
        scores = tf.squeeze(scores, axis=2, name='squeeze')
        scores = tf.sigmoid(scores, name='sigmoid')
        values, indices = tf.nn.top_k(scores, k, name='top_k')
        # get new outs
        outs = gather_idx(outs, indices, k, 'gather1')
        values = tf.expand_dims(values, 2, 'exp')
        outs = tf.multiply(values, outs, name='mul')
        # outs = tf.concat([outs, values], axis=2)
        adj_m = gather_idx(adj_m, indices, k, 'gather2')
        adj_m = tf.transpose(adj_m, perm=[0, 2, 1], name='trans')
        adj_m = gather_idx(adj_m, indices, k, 'gather3')
    return adj_m, outs


def gather_idx(outs, indices, k, scope):
    fea_num = outs.shape[-1].value
    outs = tf.reshape(outs, [-1, fea_num], name=scope+'/reshape1')
    fea_indices = tf.reshape(indices, [-1], name=scope+'/reshape2')
    outs = tf.gather(outs, fea_indices, name=scope+'/gather1')
    outs = tf.reshape(outs, [-1, k, fea_num], name=scope+'/reshape3')
    return outs


def simple_conv(adj_m, outs, num_out, rate, scope, k=1, act_fn=tf.nn.relu6):
    # adj_m = dropout(adj_m, rate, scope+'/drop1')
    outs = dropout(outs, rate, scope+'/drop2')
    cur_outs = conv1d(outs, num_out//2, k, scope+'/conv1', act_fn)
    outs = tf.matmul(adj_m, outs, name=scope+'/matmul')
    outs = conv1d(outs, num_out//2, 1, scope+'/conv2', act_fn)
    outs = tf.concat([cur_outs, outs], axis=2, name=scope+'/concat')
    return outs


def flat(outs, scope):
    return tf.layers.flatten(outs, scope+'/flat')


def conv1d(outs, num_out, k, scope, act_fn, bias=True, pad='same'):
    outs = tf.layers.conv1d(
        outs, num_out, k, activation=act_fn, name=scope+'/conv',
        padding=pad, use_bias=bias,
        kernel_initializer=tf.contrib.layers.xavier_initializer())
    return outs


def dense(outs, dim, rate, scope, act_fn=None):
    outs = dropout(outs, rate, scope+'/drop')
    outs = tf.contrib.layers.fully_connected(
        outs, dim, activation_fn=act_fn, scope=scope+'/dense',
        weights_initializer=tf.contrib.layers.xavier_initializer())
    # outs = tf.layers.dense(
    #     outs, dim, activation=act_fn, name=scope+'/dense',
    #     kernel_initializer=tf.contrib.layers.xavier_initializer())
    return outs


def dropout(outs, rate, scope):
    outs = tp.Dropout(scope+'/dp', outs, rate=rate)
    return outs


def batch_norm(outs, scope):
    outs = tf.expand_dims(outs, axis=1, name=scope+'/exp')
    outs = tp.BatchNorm(scope+'/bn', outs)
    outs = tf.squeeze(outs, axis=1, name=scope+'/squz')
    return outs
